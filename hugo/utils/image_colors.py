import requests
import colorgram
import os
import tempfile
import colorsys
import math
from typing import List, Dict, Tuple, Optional

def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def linearize(c):
    v = c / 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

def get_relative_luminance(rgb: Tuple[int, int, int]) -> float:
    # WCAG 2.0 formula
    r = linearize(rgb[0])
    g = linearize(rgb[1])
    b = linearize(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_contrast_ratio(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    l1 = get_relative_luminance(c1)
    l2 = get_relative_luminance(c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def adjust_color_for_contrast(fg: Tuple[int, int, int], bg: Tuple[int, int, int], target: float = 4.5) -> Tuple[int, int, int]:
    """
    Iteratively adjusts fg luminance to meet target contrast against bg.
    """
    current_ratio = get_contrast_ratio(fg, bg)
    if current_ratio >= target:
        return fg
        
    bg_lum = get_relative_luminance(bg)
    fg_lum = get_relative_luminance(fg)
    
    # Decide direction
    is_darkening = fg_lum < bg_lum
    
    # HSL approach preserves hue/sat
    r, g, b = fg[0]/255, fg[1]/255, fg[2]/255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    # Max iterations to prevent infinite loop
    for _ in range(20):
        if is_darkening:
            l = max(0, l - 0.05)
        else:
            l = min(1, l + 0.05)
            
        new_rgb = colorsys.hls_to_rgb(h, l, s)
        candidate = tuple(min(255, max(0, int(c * 255))) for c in new_rgb)
        
        if get_contrast_ratio(candidate, bg) >= target:
            return candidate
        
        if l == 0 or l == 1:
            break
            
    # Fallback to pure black/white if adjustment failed
    return (0, 0, 0) if is_darkening else (255, 255, 255)

def get_saturation(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    mx = max(r, g, b)
    mn = min(r, g, b)
    if mx == mn: return 0.0
    l = (mx + mn) / 2
    d = mx - mn
    if l > 127:
        return d / (510 - mx - mn)
    else:
        return d / (mx + mn)

def generate_palette_from_colors(colors: List[colorgram.Color]) -> Dict[str, str]:
    """
    Applies UX heuristics to generate a semantic color palette with WCAG AA compliance.
    """
    rgbs = [(c.rgb.r, c.rgb.g, c.rgb.b) for c in colors]
    
    vibrant_candidates = []
    neutral_candidates = []
    
    for rgb in rgbs:
        h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        is_extreme = l < 0.05 or l > 0.95
        if s > 0.15 and not is_extreme:
            vibrant_candidates.append(rgb)
        else:
            neutral_candidates.append(rgb)
            
    # 1. Primary
    if vibrant_candidates:
        primary = vibrant_candidates[0]
    elif neutral_candidates:
        filtered = [c for c in neutral_candidates if 0.1 < get_relative_luminance(c) < 0.9]
        primary = filtered[0] if filtered else neutral_candidates[0]
    else:
        primary = (50, 50, 50)

    # 2. Background (Prefer light for now)
    potential_bgs = [c for c in rgbs if get_relative_luminance(c) > 0.8]
    if potential_bgs:
        bg = potential_bgs[0]
    else:
        bg = (252, 252, 252)
        
    surface = tuple(max(0, c - 10) for c in bg)

    # 3. Secondary / Accent
    remaining_vibrant = [c for c in vibrant_candidates if c != primary]
    if remaining_vibrant:
        secondary = remaining_vibrant[0]
    else:
        secondary = primary
        
    ph, pl, ps = colorsys.rgb_to_hls(primary[0]/255, primary[1]/255, primary[2]/255)
    ah = (ph + 0.5) % 1.0
    accent_rgb = colorsys.hls_to_rgb(ah, pl, min(1.0, ps + 0.2))
    accent = tuple(int(c * 255) for c in accent_rgb)
    
    # 4. Text & Contrast Enforcement
    # Initial guess
    bg_lum = get_relative_luminance(bg)
    text = (20, 20, 20) if bg_lum > 0.5 else (240, 240, 240)
    
    # Adjust Text against BG
    text = adjust_color_for_contrast(text, bg, 4.5)
    
    # Adjust Primary Text (On-Primary)
    # Check if white works
    on_primary = (255, 255, 255)
    if get_contrast_ratio(on_primary, primary) < 4.5:
        # Check black
        if get_contrast_ratio((0, 0, 0), primary) > get_contrast_ratio(on_primary, primary):
           on_primary = (0, 0, 0)
        # If neither pass well, strict black/white is still usually best for buttons 
        # (buttons strictly need 3:1 for graphic, but text needs 4.5:1. 
        # If Primary is yellow #FFFF00, Black is 19:1. White is 1.07:1. Black wins.)

    palette = {
        'primary': rgb_to_hex(primary),
        'on-primary': rgb_to_hex(on_primary),
        'secondary': rgb_to_hex(secondary),
        'accent': rgb_to_hex(accent),
        'bg': rgb_to_hex(bg),
        'surface': rgb_to_hex(surface),
        'text': rgb_to_hex(text)
    }
    
    return palette

def generate_css_from_palette(palette: Dict[str, str]) -> str:
    """Generates CSS variables."""
    css = ":root {\n"
    for name, hex_val in palette.items():
        css += f"    --color-{name}: {hex_val};\n"
    
    # Derivatives
    css += f"    --color-muted: {palette['primary']}80;\n"
    css += f"    --color-border: {palette['text']}26;\n"
    
    css += "}\n"
    return css

def extract_colors_from_url(image_url: str) -> Tuple[Optional[Dict[str, str]], str]:
    """Downloads image, extracts colors with a11y checks."""
    try:
        if not image_url: return None, ""
        
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
            
        colors = colorgram.extract(tmp_path, 10)
        os.remove(tmp_path)
        
        if not colors: return None, ""
        
        palette = generate_palette_from_colors(colors)
        css = generate_css_from_palette(palette)
        
        return palette, css
        
    except Exception as e:
        print(f"Theme Generation Error: {e}")
        return None, ""

if __name__ == '__main__':
    # Test with Low Contrast candidate (e.g. Light Yellow logo)
    # Generic yellow image
    url = "https://placehold.co/400x400/FFFF00/000000.png" 
    print("Testing with Yellow Image...")
    palette, css = extract_colors_from_url(url)
    print("Palette:", palette)
    # Text on yellow BG should be black.
    # On-primary (Yellow) should be black.
