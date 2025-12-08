"""
Migration to add layout block definitions: section, two_col, col.
"""
from django.db import migrations


def add_block_definitions(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    blocks = [
        {
            'id': 'section',
            'label': 'Section Container',
            'icon': 'layout-template',
            'has_visual_preview': True,
            'default_params': {
                'style': 'default'
            }
        },
        {
            'id': 'two_col',
            'label': 'Two Columns',
            'icon': 'columns-2',
            'has_visual_preview': True,
            'default_params': {
                'ratio': '50-50',
                'reverse': False
            }
        },
        {
            'id': 'col',
            'label': 'Column',
            'icon': 'column',
            'has_visual_preview': True,
            'default_params': {}
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
    BlockDefinition.objects.filter(id__in=['section', 'two_col', 'col']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hugo', '0021_add_template_models'),
    ]

    operations = [
        migrations.RunPython(add_block_definitions, remove_block_definitions),
    ]
