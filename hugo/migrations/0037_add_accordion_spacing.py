"""
Add spacing parameter to accordion block
"""
from django.db import migrations


def add_accordion_spacing(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        accordion = BlockDefinition.objects.get(id='accordion')
        
        # Add spacing field to schema
        if 'fields' in accordion.schema:
            # Check if spacing field already exists
            has_spacing = any(f.get('name') == 'spacing' for f in accordion.schema['fields'])
            
            if not has_spacing:
                accordion.schema['fields'].append({
                    'name': 'spacing',
                    'type': 'select',
                    'label': 'Spacing Between Items',
                    'options': ['none', 'compact', 'normal', 'relaxed'],
                    'default': 'none'
                })
        
        # Add spacing to default_params
        if 'spacing' not in accordion.default_params:
            accordion.default_params['spacing'] = 'none'
        
        accordion.save()
        
    except BlockDefinition.DoesNotExist:
        pass  # Accordion block doesn't exist yet, skip


def reverse_accordion_spacing(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        accordion = BlockDefinition.objects.get(id='accordion')
        
        # Remove spacing field from schema
        if 'fields' in accordion.schema:
            accordion.schema['fields'] = [
                f for f in accordion.schema['fields'] if f.get('name') != 'spacing'
            ]
        
        # Remove spacing from default_params
        if 'spacing' in accordion.default_params:
            del accordion.default_params['spacing']
        
        accordion.save()
        
    except BlockDefinition.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0042_sitetemplate_theme_preset_website_theme_preset'),
    ]

    operations = [
        migrations.RunPython(add_accordion_spacing, reverse_accordion_spacing),
    ]

