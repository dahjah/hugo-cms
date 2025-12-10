"""
Pipeline Runner

Main entry point that orchestrates all pipeline stages.
Each stage is independently callable, and this module ties them together.
"""
import os
import sys
from typing import List, Optional

# Django setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from hugo.schemas import BusinessProfile
from hugo.pipeline.orchestrator import orchestrate
from hugo.pipeline.colors import generate_colors
from hugo.pipeline.selector import select_template
from hugo.pipeline.mapper import map_profile_to_blocks
from hugo.pipeline.builder import build_site


def run_pipeline(
    inputs: List[str],
    template_choice: Optional[str] = None,
    categories: Optional[List[str]] = None,
    skip_colors: bool = False,
    media_root: str = 'media'
) -> dict:
    """
    Execute the full site generation pipeline.
    
    Args:
        inputs: List of URLs/identifiers (Yelp, Instagram, FTL, etc.)
        template_choice: Optional explicit template slug
        categories: Optional categories for template selection (if not from scraping)
        skip_colors: If True, skip color extraction (use template defaults)
        media_root: Base path for media storage
    
    Returns:
        Dict with 'profile', 'template', 'website' keys
    """
    print("=" * 60)
    print("PIPELINE: Starting site generation")
    print("=" * 60)
    
    # Stage 1: Scrape & Aggregate
    print("\n[Stage 1] Orchestrating scrapers...")
    profile = orchestrate(inputs)
    print(f"  → Name: {profile.name}")
    print(f"  → Slug: {profile.slug}")
    print(f"  → Categories: {profile.categories}")
    
    # Override categories if provided
    if categories:
        profile.categories = categories
    
    # Stage 2: Generate Colors
    if not skip_colors:
        print("\n[Stage 2] Generating colors...")
        profile = generate_colors(profile, media_root=media_root)
    else:
        print("\n[Stage 2] Skipping colors (using template defaults)")
    
    # Stage 3: Select Template
    print("\n[Stage 3] Selecting template...")
    template_slug = select_template(profile, explicit_choice=template_choice)
    print(f"  → Template: {template_slug}")
    
    # Stage 4: Map Content
    print("\n[Stage 4] Mapping content to template...")
    block_overrides = map_profile_to_blocks(profile, template_slug)
    
    # Stage 5: Build Site
    print("\n[Stage 5] Building site...")
    website = build_site(
        profile_name=profile.name,
        profile_slug=profile.slug,
        template_slug=template_slug,
        block_overrides=block_overrides,
        base_css=profile.colors_css
    )
    
    print("\n" + "=" * 60)
    print(f"✅ PIPELINE COMPLETE")
    print(f"   Website: {website.name}")
    print(f"   URL: http://localhost:8000/cms/website/{website.id}/")
    print("=" * 60)
    
    return {
        'profile': profile,
        'template': template_slug,
        'website': website
    }


# CLI Interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate website from source URLs")
    parser.add_argument('inputs', nargs='+', help="URLs or identifiers (Yelp, Instagram, FTL)")
    parser.add_argument('--template', help="Explicit template slug to use")
    parser.add_argument('--categories', nargs='*', help="Categories for template selection")
    parser.add_argument('--skip-colors', action='store_true', help="Skip color extraction")
    
    args = parser.parse_args()
    
    result = run_pipeline(
        inputs=args.inputs,
        template_choice=args.template,
        categories=args.categories,
        skip_colors=args.skip_colors
    )
