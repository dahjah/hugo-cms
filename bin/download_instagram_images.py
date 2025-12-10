#!/usr/bin/env python3
"""
Download Instagram images for Strippin Dippin Chicken and update website blocks
"""
import os
import sys
import requests
import uuid
from pathlib import Path
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from hugo.models import Website, BlockInstance, UploadedFile

# HikerAPI config
API_KEY = "1b42yowz11l52wmybh4x8e2ujp4kj49g"
API_BASE = "https://api.hikerapi.com"
HEADERS = {"x-access-key": API_KEY}

def download_image(url, filename):
    """Download image from URL and save to media directory"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Create media directory for strippin-dippin
        media_dir = Path(settings.MEDIA_ROOT) / 'strippin_dippin'
        media_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = media_dir / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return str(filepath), len(response.content)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None, 0

def main():
    print("Fetching Instagram data for @strippindippinchicken...")
    
    # Get user profile data
    response = requests.get(
        f"{API_BASE}/a2/user",
        params={"username": "strippindippinchicken"},
        headers=HEADERS
    )
    
    if response.status_code != 200:
        print(f"Error fetching profile: {response.status_code}")
        return
    
    data = response.json()
    # Navigate the graphql response structure
    user_data = data.get('graphql', {}).get('user', {})
    
    if not user_data:
        print("Error: No user data found in response")
        print(f"Response keys: {list(data.keys())}")
        return
    
    # Get profile picture (logo)
    logo_url = user_data.get('profile_pic_url_hd')
    print(f"Profile pic URL: {logo_url[:80] if logo_url else 'None'}...")
    
    # Download logo
    logo_path, logo_size = download_image(logo_url, "logo.jpg") if logo_url else (None, 0)
    
    # Get recent posts for food photos
    posts = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
    print(f"Found {len(posts)} recent posts")

    
    # Download first 6 food photos (skip videos)
    food_photos = []
    for i, post in enumerate(posts[:10]):  # Check first 10
        node = post.get('node', {})
        if node.get('__typename') == 'GraphImage':  # Only images, not videos
            img_url = node.get('display_url')
            if img_url:
                photo_path, photo_size = download_image(img_url, f"food_{i+1}.jpg")
                if photo_path:
                    food_photos.append(photo_path)
                    print(f"Downloaded food photo {i+1}")
                if len(food_photos) >= 6:
                    break
    
    # Get website
    website = Website.objects.get(slug='strippin-dippin-chicken')
    
    # Create UploadedFile records
    uploaded_images = {}
    
    if logo_path:
        rel_path = f"strippin_dippin/logo.jpg"
        uf, _ = UploadedFile.objects.get_or_create(
            website=website,
            file_path=rel_path,
            defaults={
                'filename': 'logo.jpg',
                'file_url': f"/media/{rel_path}",
                'file_size': logo_size,
                'content_type': 'image/jpeg'
            }
        )
        uploaded_images['logo'] = uf.file_url
        print(f"✓ Logo registered: {uf.file_url}")
    
    for i, photo_path in enumerate(food_photos):
        rel_path = f"strippin_dippin/food_{i+1}.jpg"
        uf, _ = UploadedFile.objects.get_or_create(
            website=website,
            file_path=rel_path,
            defaults={
                'filename': f'food_{i+1}.jpg',
                'file_url': f"/media/{rel_path}",
                'file_size': Path(photo_path).stat().st_size,
                'content_type': 'image/jpeg'
            }
        )
        uploaded_images[f'food_{i+1}'] = uf.file_url
        print(f"✓ Food photo {i+1} registered: {uf.file_url}")
    
    # Update website blocks with images
    print("\nUpdating website blocks...")
    
    # Update logo in headers
    brand_logos = BlockInstance.objects.filter(
        page__website=website,
        definition_id='brand_logo'
    )
    for logo_block in brand_logos:
        logo_block.params['logo_image'] = uploaded_images.get('logo', '')
        logo_block.save()
        print(f"✓ Updated logo in brand_logo block")
    
    # Update hero backgrounds
    heroes = BlockInstance.objects.filter(
        page__website=website,
        definition_id='hero'
    )
    for i, hero in enumerate(heroes):
        # Use different food photos for different hero sections
        food_key = f'food_{min(i+1, len(food_photos))}'
        hero.params['bgImage'] = uploaded_images.get(food_key, '')
        hero.save()
        print(f"✓ Updated hero background")
    
    # Update menu items
    menu_grids = BlockInstance.objects.filter(
        page__website=website,
        definition_id='menu_grid'
    )
    
    for menu_grid in menu_grids:
        items = menu_grid.params.get('items', [])
        for i, item in enumerate(items):
            if i < len(food_photos):
                food_key = f'food_{i+1}'
                item['image'] = uploaded_images.get(food_key, '')
        menu_grid.params['items'] = items
        menu_grid.save()
        print(f"✓ Updated menu grid images ({len(items)} items)")
    
    print(f"\n✅ Success! Downloaded {len(food_photos)} food photos and 1 logo")
    print(f"✅ Updated all website blocks with images")
    print(f"\nImages saved to: {settings.MEDIA_ROOT}/strippin_dippin/")

if __name__ == '__main__':
    main()
