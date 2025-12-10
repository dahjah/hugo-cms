#!/usr/bin/env python3
"""
Download images from Food Truck League and update hero blocks
"""
import os
import sys
import requests
from pathlib import Path
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from hugo.models import Website, BlockInstance, UploadedFile

def download_image(url, filename):
    """Download image from URL and save to media directory"""
    try:
        # Make URL absolute if relative
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://foodtruckleague.com' + url
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Create media directory
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
    print("Fetching Food Truck League page...")
    
    response = requests.get('https://foodtruckleague.com/Utah/trucks/677ec632f7fd49c21152b236')
    html = response.text
    
    # Find all image sources using regex
    import re
    images = []
    
    # Find img src attributes
    img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    images.extend(img_srcs)
    
    # Find data-src attributes (lazy loading)
    data_srcs = re.findall(r'data-src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    images.extend(data_srcs)
    
    # Find background-image URLs  
    bg_images = re.findall(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', html, re.IGNORECASE)
    images.extend(bg_images)
    
    # Filter for likely truck/food images (exclude logos, icons, etc.)
    filtered_images = []
    for img in images:
        img_lower = img.lower()
        # Skip small icons, logos, etc.
        if any(x in img_lower for x in ['logo', 'icon', 'avatar', 'badge', 'flag']):
            continue
        # Include images that look like photos
        if any(x in img_lower for x in ['.jpg', '.jpeg', '.png', 'photo', 'image', 'truck', 'food']):
            filtered_images.append(img)
        # Also include images from CDN/storage that are likely photos
        elif any(x in img_lower for x in ['cloudinary', 'amazonaws', 'storage', 'cdn']):
            if not any(x in img_lower for x in ['thumb', 'avatar', 'icon']):
                filtered_images.append(img)
    
    print(f"Found {len(images)} total images, {len(filtered_images)} potential hero images")
    
    if filtered_images:
        print("\nSample images found:")
        for img in filtered_images[:3]:
            print(f"  - {img[:80]}...")
    
    # Download up to 2 hero images
    hero_images = []
    for i, img_url in enumerate(filtered_images[:5]):  # Try first 5
        print(f"\nAttempting to download image {i+1}...")
        filepath, size = download_image(img_url, f"hero_{i+1}.jpg")
        if filepath and size > 10000:  # Only keep images > 10KB
            hero_images.append(filepath)
            print(f"  ✓ Downloaded ({size} bytes)")
            if len(hero_images) >= 2:  # Get 2 hero images
                break
        else:
            print(f"  ✗ Skipped (too small or failed)")

    
    if not hero_images:
        print("❌ No suitable images found on Food Truck League page")
        return
    
    # Get website
    website = Website.objects.get(slug='strippin-dippin-chicken')
    
    # Register images
    uploaded_images = []
    for i, img_path in enumerate(hero_images):
        rel_path = f"strippin_dippin/hero_{i+1}.jpg"
        uf, _ = UploadedFile.objects.get_or_create(
            website=website,
            file_path=rel_path,
            defaults={
                'filename': f'hero_{i+1}.jpg',
                'file_url': f"/media/{rel_path}",
                'file_size': Path(img_path).stat().st_size,
                'content_type': 'image/jpeg'
            }
        )
        uploaded_images.append(uf.file_url)
        print(f"✓ Registered: {uf.file_url}")
    
    # Update hero blocks
    heroes = BlockInstance.objects.filter(
        page__website=website,
        definition_id='hero'
    ).order_by('id')
    
    for i, hero in enumerate(heroes):
        if i < len(uploaded_images):
            hero.params['bgImage'] = uploaded_images[i]
            hero.save()
            print(f"✓ Updated hero block {i+1} background")
    
    print(f"\n✅ Success! Downloaded {len(hero_images)} hero images from Food Truck League")
    print(f"✅ Updated {min(len(heroes), len(uploaded_images))} hero blocks")

if __name__ == '__main__':
    main()
