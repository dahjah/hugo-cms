#!/usr/bin/env python3
"""
Add global header and footer to Strippin Dippin Chicken website
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website, BlockInstance

def main():
    website = Website.objects.get(slug='strippin-dippin-chicken')
    
    # Check if global blocks already exist
    existing_global = BlockInstance.objects.filter(website=website, page=None)
    if existing_global.exists():
        print(f"Deleting {existing_global.count()} existing global blocks...")
        existing_global.delete()
    
    # Get logo URL from existing blocks
    existing_logo = BlockInstance.objects.filter(
        page__website=website,
        definition_id='brand_logo'
    ).first()
    
    logo_url = existing_logo.params.get('logo_image', '') if existing_logo else '/media/strippin_dippin/logo.jpg'
    
    print("Creating global header...")
    # Create global header row
    header_row = BlockInstance.objects.create(
        website=website,
        page=None,  # Global block
        definition_id='row',
        placement_key='header',
        sort_order=0,
        params={
            'gap': '4',
            'justify': 'space-between',
            'align': 'center'
        }
    )
    
    # Brand logo in header
    BlockInstance.objects.create(
        website=website,
        page=None,
        parent=header_row,
        definition_id='brand_logo',
        placement_key='column',
        sort_order=0,
        params={
            'brand_name': 'Strippin Dippin Chicken',
            'logo_image': logo_url,
            'link_url': '/'
        }
    )
    
    # Menu in header
    BlockInstance.objects.create(
        website=website,
        page=None,
        parent=header_row,
        definition_id='menu',
        placement_key='column',
        sort_order=1,
        params={
            'style': 'pills',
            'responsive': True,
            'items': [
                {'label': 'Home', 'url': '/', 'type': 'link'},
                {'label': 'Menu', 'url': '/menu', 'type': 'link'},
                {'label': 'Find Us', 'url': '/#location', 'type': 'link'}
            ]
        }
    )
    
    print("Creating global footer...")
    # Footer text
    BlockInstance.objects.create(
        website=website,
        page=None,
        definition_id='text',
        placement_key='footer',
        sort_order=0,
        params={
            'content': '<p><strong>Strippin Dippin Chicken</strong><br>West Jordan, UT Area (Mobile Food Truck)<br>Follow us on Instagram for daily location and hours</p>'
        }
    )
    
    # Footer social links
    BlockInstance.objects.create(
        website=website,
        page=None,
        definition_id='social_links',
        placement_key='footer',
        sort_order=1,
        params={
            'links': [
                {'platform': 'instagram', 'url': 'https://www.instagram.com/strippindippinchicken/'},
                {'platform': 'yelp', 'url': 'https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan'}
            ]
        }
    )
    
    # Delete page-specific header/footer blocks since we now have global ones
    page_headers = BlockInstance.objects.filter(
        page__website=website,
        placement_key__in=['header', 'footer'],
        parent=None  # Only top-level blocks
    )
    
    deleted_count = page_headers.count()
    if deleted_count > 0:
        print(f"Removing {deleted_count} page-specific header/footer blocks...")
        page_headers.delete()
    
    # Count final blocks
    global_blocks = BlockInstance.objects.filter(website=website, page=None)
    print(f"\n✅ Success!")
    print(f"Created {global_blocks.count()} global blocks")
    print(f"  - Header: 1 row with logo + menu")
    print(f"  - Footer: 1 text + 1 social links")

if __name__ == '__main__':
    main()
