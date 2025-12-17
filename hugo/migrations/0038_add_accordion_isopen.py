"""
Add _isOpen field to accordion item schema
"""
from django.db import migrations


def add_accordion_isopen(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        accordion = BlockDefinition.objects.get(id='accordion')
        
        # Update the item_schema to include _isOpen
        if 'fields' in accordion.schema:
            for field in accordion.schema['fields']:
                if field.get('name') == 'items' and 'item_schema' in field:
                    # Add _isOpen to item_schema
                    field['item_schema']['_isOpen'] = {
                        'type': 'boolean',
                        'label': 'Start Open'
                    }
        
        accordion.save()
        
    except BlockDefinition.DoesNotExist:
        pass


def reverse_accordion_isopen(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        accordion = BlockDefinition.objects.get(id='accordion')
        
        # Remove _isOpen from item_schema
        if 'fields' in accordion.schema:
            for field in accordion.schema['fields']:
                if field.get('name') == 'items' and 'item_schema' in field:
                    if '_isOpen' in field['item_schema']:
                        del field['item_schema']['_isOpen']
        
        accordion.save()
        
    except BlockDefinition.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0037_add_accordion_spacing'),
    ]

    operations = [
        migrations.RunPython(add_accordion_isopen, reverse_accordion_isopen),
    ]
