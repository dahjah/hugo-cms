"""
Site Builder

Takes mapped content and creates the actual Website in Django.
"""
import os
import django

# Django setup for standalone usage
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from typing import Dict, Any
from hugo.models import Website, Page, BlockInstance
from hugo.template_service import create_website_from_template


def build_site(
    profile_name: str,
    profile_slug: str,
    template_slug: str,
    block_overrides: Dict[str, Any],
    base_css: str = ""
) -> Website:
    """
    Create website from template and apply profile-specific overrides.
    
    Args:
        profile_name: Display name for website
        profile_slug: URL slug for website
        template_slug: Template to use
        block_overrides: Dict from ContentMapper with block params
        base_css: CSS variables from ColorGenerator
    
    Returns:
        Created Website instance
    """
    print(f"[SiteBuilder] Creating site: {profile_name} ({profile_slug})")
    
    # Create base website from template
    website = create_website_from_template(
        template_slug=template_slug,
        website_name=profile_name,
        website_slug=profile_slug
    )
    
    # Apply CSS
    if base_css:
        website.custom_css = base_css
        website.save()
        print("[SiteBuilder] ✓ Applied color theme")
    
    # Apply block overrides
    pages_overrides = block_overrides.get('pages', {})
    global_overrides = block_overrides.get('global', {})
    
    # Update page blocks
    for page_slug, blocks in pages_overrides.items():
        try:
            page = Page.objects.get(website=website, slug=page_slug)
            _apply_block_overrides(page, blocks)
        except Page.DoesNotExist:
            print(f"[SiteBuilder] Warning: Page '{page_slug}' not found in template")
    
    # Update global blocks (footer, social_links, etc.)
    for block_def_id, params in global_overrides.items():
        block = BlockInstance.objects.filter(
            website=website,
            page=None,
            definition_id=block_def_id
        ).first()
        
        if block:
            block.params.update(params)
            block.save()
            print(f"[SiteBuilder] ✓ Updated global {block_def_id}")
        else:
            # Try matching by placement_key
            block = BlockInstance.objects.filter(
                website=website,
                page=None,
                placement_key=block_def_id
            ).first()
            if block:
                block.params.update(params)
                block.save()
                print(f"[SiteBuilder] ✓ Updated global {block_def_id} (by placement)")
    
    print(f"[SiteBuilder] ✓ Website created: ID={website.id}")
    return website


def _apply_block_overrides(page: Page, blocks: Dict[str, Dict]):
    """Apply parameter overrides to blocks on a page."""
    for block_def_id, params in blocks.items():
        block = BlockInstance.objects.filter(
            page=page,
            definition_id=block_def_id
        ).first()
        
        if block and params:
            block.params.update(params)
            block.save()
            print(f"[SiteBuilder] ✓ Updated {page.slug}/{block_def_id}")
        else:
            print(f"[SiteBuilder] Warning: Block '{block_def_id}' not found on {page.slug}")
