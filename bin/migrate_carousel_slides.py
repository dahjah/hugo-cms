#!/usr/bin/env python3
"""
Migrate carousel slides from JSON to BlockInstance children.

This script converts existing carousel blocks that store slides in params.slides
to use BlockInstance children with placement_key='slide_N' for consistency.
"""
import os
import django
import sys

sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import BlockInstance, BlockDefinition
from django.db import transaction


@transaction.atomic
def migrate_carousel_slides():
    """Convert carousel JSON slides to BlockInstance children."""
    
    carousels = BlockInstance.objects.filter(definition_id='carousel')
    total_carousels = carousels.count()
    total_slides_migrated = 0
    
    print(f"Found {total_carousels} carousel blocks to migrate")
    
    for carousel in carousels:
        slides = carousel.params.get('slides', [])
        
        if not slides:
            print(f"  Carousel {carousel.id}: No slides to migrate")
            continue
        
        print(f"  Carousel {carousel.id}: Migrating {len(slides)} slides")
        
        for slide_idx, slide in enumerate(slides):
            slide_children = slide.get('children', [])
            
            for child_idx, child_data in enumerate(slide_children):
                child_type = child_data.get('type')
                child_params = child_data.get('params', {})
                
                if not child_type:
                    print(f"    WARNING: Slide {slide_idx} child {child_idx} has no type, skipping")
                    continue
                
                # Get block definition
                try:
                    definition = BlockDefinition.objects.get(id=child_type)
                except BlockDefinition.DoesNotExist:
                    print(f"    WARNING: Block definition '{child_type}' not found, skipping")
                    continue
                
                # Create BlockInstance for this slide child
                BlockInstance.objects.create(
                    definition=definition,
                    parent=carousel,
                    website=carousel.website,
                    page=None,  # Child blocks don't link to page
                    placement_key=f'slide_{slide_idx}',
                    sort_order=child_idx,
                    params=child_params
                )
                
                total_slides_migrated += 1
                print(f"    Created {child_type} for slide {slide_idx}")
        
        # Remove the JSON slides from params
        carousel.params.pop('slides', None)
        carousel.save()
        print(f"  Carousel {carousel.id}: Migration complete, removed JSON slides")
    
    print(f"\n✓ Migration complete: {total_carousels} carousels, {total_slides_migrated} slide children created")


if __name__ == '__main__':
    print("Starting carousel migration...")
    migrate_carousel_slides()
