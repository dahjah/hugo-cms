"""
Migration to add new block definitions for cairnscounseling template import.
Adds: carousel, testimonial, flip_cards, accordion, section, cta
"""
from django.db import migrations


def add_block_definitions(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    blocks = [
        {
            'id': 'carousel',
            'label': 'Carousel',
            'icon': 'gallery-horizontal',
            'has_visual_preview': True,
            'default_params': {
                'auto_advance': True,
                'interval_seconds': 8,
                'show_dots': True,
                'show_arrows': True
            }
        },
        {
            'id': 'testimonial',
            'label': 'Testimonial',
            'icon': 'message-circle-heart',
            'has_visual_preview': True,
            'default_params': {
                'quote': '',
                'author': ''
            }
        },
        {
            'id': 'flip_cards',
            'label': 'Flip Cards Grid',
            'icon': 'flip-horizontal',
            'has_visual_preview': True,
            'default_params': {
                'cards': [],
                'columns': 3
            }
        },
        {
            'id': 'accordion',
            'label': 'Accordion/FAQ',
            'icon': 'chevrons-down-up',
            'has_visual_preview': True,
            'default_params': {
                'items': [],
                'allow_multiple': False
            }
        },
    ]
    
    for block_data in blocks:
        BlockDefinition.objects.update_or_create(
            id=block_data['id'],
            defaults={
                'label': block_data['label'],
                'icon': block_data['icon'],
                'has_visual_preview': block_data['has_visual_preview'],
                'default_params': block_data['default_params']
            }
        )


def remove_block_definitions(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    BlockDefinition.objects.filter(id__in=[
        'carousel', 'testimonial', 'flip_cards', 'accordion'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hugo', '0019_add_pages_support'),
    ]

    operations = [
        migrations.RunPython(add_block_definitions, remove_block_definitions),
    ]
