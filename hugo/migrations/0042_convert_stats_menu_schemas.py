"""
Convert stats_counter and menu_grid schemas to Vue-compatible format
"""
from django.db import migrations


def convert_schemas_to_vue_format(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    # Convert stats_counter
    try:
        stats = BlockDefinition.objects.get(id='stats_counter')
        stats.schema = {
            'fields': [
                {
                    'name': 'stats',
                    'type': 'array',
                    'label': 'Stats',
                    'item_schema': {
                        'value': 'text',
                        'suffix': 'text',
                        'label': 'text'
                    }
                }
            ]
        }
        stats.save()
    except BlockDefinition.DoesNotExist:
        pass
    
    # Convert menu_grid
    try:
        menu = BlockDefinition.objects.get(id='menu_grid')
        menu.schema = {
            'fields': [
                {
                    'name': 'title',
                    'type': 'text',
                    'label': 'Title'
                },
                {
                    'name': 'items',
                    'type': 'array',
                    'label': 'Menu Items',
                    'item_schema': {
                        'name': 'text',
                        'image': 'image',
                        'description': 'textarea'
                    }
                }
            ]
        }
        menu.save()
    except BlockDefinition.DoesNotExist:
        pass


def reverse_schemas(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    # Revert stats_counter
    try:
        stats = BlockDefinition.objects.get(id='stats_counter')
        stats.schema = {
            'type': 'object',
            'properties': {
                'stats': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'value': {'type': 'string'},
                            'suffix': {'type': 'string'},
                            'label': {'type': 'string'}
                        }
                    }
                }
            }
        }
        stats.save()
    except BlockDefinition.DoesNotExist:
        pass
    
    # Revert menu_grid
    try:
        menu = BlockDefinition.objects.get(id='menu_grid')
        menu.schema = {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'image': {'type': 'string', 'format': 'uri'},
                            'description': {'type': 'text'}
                        }
                    }
                }
            }
        }
        menu.save()
    except BlockDefinition.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0041_remove_alert_style_orientation'),
    ]

    operations = [
        migrations.RunPython(convert_schemas_to_vue_format, reverse_schemas),
    ]
