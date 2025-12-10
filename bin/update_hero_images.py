#!/usr/bin/env python3
"""
Update hero blocks with Instagram food photos since FTL images are protected
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
    
    # Get hero blocks
    heroes = BlockInstance.objects.filter(
        page__website=website,
        definition_id='hero'
    ).order_by('id')
    
    # Use Instagram food photos for hero backgrounds
    # We have food_1 through food_6 available
    hero_images = [
        '/media/strippin_dippin/food_3.jpg',  # Home page hero
        '/media/strippin_dippin/food_5.jpg',  # Menu page hero
    ]
    
    print(f"Found {heroes.count()} hero blocks")
    
    updated = 0
    for i, hero in enumerate(heroes):
        if i < len(hero_images):
            old_bg = hero.params.get('bgImage', '')
            hero.params['bgImage'] = hero_images[i]
            hero.save()
            print(f"✓ Updated hero {i+1}:")
            print(f"    Old: {old_bg if old_bg else 'NO IMAGE'}")
            print(f"    New: {hero_images[i]}")
            updated += 1
    
    print(f"\n✅ Updated {updated} hero blocks with Instagram food photos")

if __name__ == '__main__':
    main()
