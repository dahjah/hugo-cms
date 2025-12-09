#!/usr/bin/env python
"""
Test script to import a Hugo site with TOML frontmatter.
This tests the toml_importer module.
"""
import os
import django
import sys
from pathlib import Path

sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website
from hugo.toml_importer import import_toml_site

def test_import():
    """Import wadatnchew site from hugo_output"""
    slug = 'wadatnchew-test'
    name = 'Wadatnchew Test Import'
    
    # Delete existing test import if it exists
    try:
        ws = Website.objects.get(slug=slug)
        print(f"✗ Deleting existing test website: {ws.name}")
        ws.delete()
    except Website.DoesNotExist:
        print(f"✓ No existing website with slug '{slug}'")
    
    # Import
    print("\n" + "="*60)
    print(f"Importing Wadatnchew site from TOML as '{name}'...")
    print("="*60)
    
    hugo_root = '/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms/hugo_output/wadatnchew'
    
    try:
        website = import_toml_site(hugo_root, name, slug)
        
        print(f"\n✓ Successfully imported: {website.name}")
        print(f"  - Slug: {website.slug}")
        
        # Show imported pages
        from hugo.models import Page, BlockInstance
        pages = Page.objects.filter(website=website)
        print(f"\n  Pages imported: {pages.count()}")
        for page in pages:
            block_count = BlockInstance.objects.filter(page=page).count()
            print(f"    - {page.title} ({page.slug}): {block_count} root blocks")
        
        # Check for carousel blocks
        from hugo.models import BlockDefinition
        carousel_def = BlockDefinition.objects.get(id='carousel')
        carousels = BlockInstance.objects.filter(website=website, definition=carousel_def)
        print(f"\n  Carousels found: {carousels.count()}")
        for carousel in carousels:
            slides = carousel.params.get('slides', [])
            print(f"    - Carousel {carousel.id}: {len(slides)} slides")
            for idx, slide in enumerate(slides):
                children = slide.get('children', [])
                if children:
                    child_types = [c.get('type') for c in children]
                    print(f"      Slide {idx}: {', '.join(child_types)}")
        
        print("\n" + "="*60)
        print("✓ IMPORT SUCCESSFUL!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)
