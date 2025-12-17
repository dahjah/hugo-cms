"""
Fix _isOpen field format in accordion item schema
"""
from django.db import migrations


def fix_accordion_isopen_format(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        accordion = BlockDefinition.objects.get(id='accordion')
        
        # Update the item_schema to use correct format for _isOpen
        if 'fields' in accordion.schema:
            for field in accordion.schema['fields']:
                if field.get('name') == 'items' and 'item_schema' in field:
                    # Change from object format to simple string format
                    field['item_schema']['_isOpen'] = 'boolean'
        
        accordion.save()
        
    except BlockDefinition.DoesNotExist:
        pass


def reverse_accordion_isopen_format(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        accordion = BlockDefinition.objects.get(id='accordion')
        
        # Revert to object format
        if 'fields' in accordion.schema:
            for field in accordion.schema['fields']:
                if field.get('name') == 'items' and 'item_schema' in field:
                    field['item_schema']['_isOpen'] = {
                        'type': 'boolean',
                        'label': 'Start Open'
                    }
        
        accordion.save()
        
    except BlockDefinition.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0038_add_accordion_isopen'),
    ]

    operations = [
        migrations.RunPython(fix_accordion_isopen_format, reverse_accordion_isopen_format),
    ]
