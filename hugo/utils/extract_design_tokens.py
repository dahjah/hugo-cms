#!/usr/bin/env python
"""
Dembrandt Integration Utility

Extracts design tokens from a website using dembrandt and converts them
to the base_css format used by SiteTemplate.

Usage:
    python extract_design_tokens.py https://cairnscounselingcenter.com
    python extract_design_tokens.py https://mambotruck.com --save

Requires: Node.js 18+ and npx available in PATH
"""
import argparse
import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any


def run_dembrandt(url: str, save_output: bool = False) -> Optional[Dict[str, Any]]:
    """
    Run dembrandt on a URL and return the extracted design tokens.
    Uses --save-output with a temp directory for reliable JSON parsing.
    """
    import tempfile
    import glob
    
    print(f"Running dembrandt on {url}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use bash to source nvm and run with correct Node version
        # dembrandt saves output to: output/{domain}/YYYY-MM-DDTHH-MM-SS.json
        cmd = f'source ~/.nvm/nvm.sh && nvm use 20 > /dev/null 2>&1 && dembrandt {url} --save-output'
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True,
                executable='/bin/bash',
                cwd=tmpdir,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                print(f"Error running dembrandt: {result.stderr}")
                return None
            
            # Find the JSON file in the output directory
            json_files = glob.glob(f'{tmpdir}/output/**/*.json', recursive=True)
            
            if not json_files:
                print(f"No JSON output file found in {tmpdir}/output/")
                print(f"stdout: {result.stdout[:500]}...")
                return None
            
            # Read the most recent JSON file (should only be one)
            json_file = json_files[0]
            with open(json_file) as f:
                tokens = json.load(f)
            
            return tokens
                
        except subprocess.TimeoutExpired:
            print("Dembrandt timed out after 2 minutes")
            return None
        except FileNotFoundError:
            print("Could not find npx. Please ensure Node.js 18+ is installed and npx is in PATH.")
            return None
        except json.JSONDecodeError as e:
            print(f"Could not parse dembrandt JSON output: {e}")
            return None


def tokens_to_base_css(tokens: Dict[str, Any]) -> str:
    """
    Convert dembrandt tokens to CSS custom properties format.
    """
    css_lines = [":root {"]
    
    # Extract colors
    colors = tokens.get("colors", {})
    
    # Color palette - use normalized hex value
    palette = colors.get("palette", [])
    color_names = ["primary", "secondary", "accent", "bg", "text", "muted", "border", "highlight"]
    high_confidence = [c for c in palette if c.get("confidence") == "high"]
    
    for i, color in enumerate(high_confidence[:8]):
        hex_val = color.get("normalized") or color.get("color")
        if hex_val and i < len(color_names):
            css_lines.append(f"    --color-{color_names[i]}: {hex_val};")
    
    # CSS variables from the site
    css_vars = colors.get("cssVariables", {})
    for var_name, var_value in list(css_vars.items())[:10]:
        # Clean up variable name
        clean_name = var_name.replace("--color-", "").replace("--", "")
        if len(clean_name) > 10:  # Skip auto-generated ugly names
            continue
        css_lines.append(f"    --color-site-{clean_name}: {var_value};")
    
    css_lines.append("")
    
    # Typography - extract from styles array
    typography = tokens.get("typography", {})
    styles = typography.get("styles", [])
    
    # Extract unique font families
    fonts_seen = []
    for style in styles:
        family = style.get("family")
        if family and family not in fonts_seen:
            fonts_seen.append(family)
    
    for i, family in enumerate(fonts_seen[:3]):
        name = ["primary", "secondary", "accent"][i]
        css_lines.append(f"    --font-{name}: \"{family}\", sans-serif;")
    
    # Extract font sizes
    sizes_seen = set()
    for style in styles:
        size = style.get("size")
        if size:
            # Extract just the px value (e.g., "65px (4.06rem)" -> "65px")
            size_val = size.split(" ")[0] if " " in size else size
            sizes_seen.add(size_val)
    
    try:
        sorted_sizes = sorted(list(sizes_seen), key=lambda x: float(x.replace("px", "").replace("rem", "").replace("em", "") or 0))
    except (ValueError, AttributeError):
        sorted_sizes = list(sizes_seen)
    
    size_names = ["xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"]
    for i, size in enumerate(sorted_sizes[:8]):
        if i < len(size_names):
            css_lines.append(f"    --text-{size_names[i]}: {size};")
    
    css_lines.append("")
    
    # Spacing
    spacing = tokens.get("spacing", {})
    scale = spacing.get("scale", [])
    for i, space in enumerate(scale[:8]):
        if space:
            css_lines.append(f"    --space-{i + 1}: {space};")
    
    css_lines.append("")
    
    # Borders
    borders = tokens.get("borders", {})
    radius = borders.get("radius", [])
    if radius:
        css_lines.append(f"    --radius-sm: {radius[0] if radius else '4px'};")
        if len(radius) > 1:
            css_lines.append(f"    --radius-md: {radius[1]};")
        if len(radius) > 2:
            css_lines.append(f"    --radius-lg: {radius[2]};")
    
    css_lines.append("")
    
    # Shadows
    shadows = tokens.get("shadows", [])
    for i, shadow in enumerate(shadows[:3]):
        if isinstance(shadow, dict):
            shadow_val = shadow.get("value") or shadow.get("css")
        else:
            shadow_val = shadow
        if shadow_val:
            shadow_name = ["sm", "md", "lg"][i] if i < 3 else str(i)
            css_lines.append(f"    --shadow-{shadow_name}: {shadow_val};")
    
    css_lines.append("}")
    
    return "\n".join(css_lines)


def extract_logo_url(tokens: Dict[str, Any]) -> Optional[str]:
    """
    Extract logo URL from dembrandt tokens if available.
    """
    # Check various places dembrandt might put logo info
    logo = tokens.get("logo")
    if logo:
        if isinstance(logo, str):
            return logo
        elif isinstance(logo, dict):
            return logo.get("url") or logo.get("src")
    
    # Check in brand section
    brand = tokens.get("brand", {})
    if brand.get("logo"):
        return brand["logo"]
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Extract design tokens from a website")
    parser.add_argument("url", help="URL to extract design tokens from")
    parser.add_argument("--save", action="store_true", help="Save raw JSON output")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of CSS")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    # Run dembrandt
    tokens = run_dembrandt(args.url, save_output=args.save)
    
    if not tokens:
        print("Failed to extract design tokens")
        sys.exit(1)
    
    if args.json:
        output = json.dumps(tokens, indent=2)
    else:
        output = tokens_to_base_css(tokens)
        
        # Also print logo if found
        logo_url = extract_logo_url(tokens)
        if logo_url:
            print(f"\nLogo URL: {logo_url}")
    
    if args.output:
        Path(args.output).write_text(output)
        print(f"\nSaved to {args.output}")
    else:
        print("\n" + "=" * 60)
        print("EXTRACTED CSS TOKENS:")
        print("=" * 60)
        print(output)
    
    return tokens


if __name__ == "__main__":
    main()
