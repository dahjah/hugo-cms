"""
Add style and orientation fields to alert block
"""
from django.db import migrations


def add_alert_style_orientation(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        alert = BlockDefinition.objects.get(id='alert')
        
        # Add style and orientation fields to schema
        if 'fields' in alert.schema:
            # Check if fields already exist
            has_style = any(f.get('name') == 'style' for f in alert.schema['fields'])
            has_orientation = any(f.get('name') == 'orientation' for f in alert.schema['fields'])
            
            if not has_style:
                alert.schema['fields'].append({
                    'name': 'style',
                    'type': 'select',
                    'label': 'Style',
                    'options': ['normal', 'dash', 'soft'],
                    'default': 'normal'
                })
            
            if not has_orientation:
                alert.schema['fields'].append({
                    'name': 'orientation',
                    'type': 'select',
                    'label': 'Orientation',
                    'options': ['horizontal', 'vertical'],
                    'default': 'horizontal'
                })
        
        # Add to default_params
        if 'style' not in alert.default_params:
            alert.default_params['style'] = 'normal'
        if 'orientation' not in alert.default_params:
            alert.default_params['orientation'] = 'horizontal'
        
        alert.save()
        
    except BlockDefinition.DoesNotExist:
        pass


def reverse_alert_style_orientation(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        alert = BlockDefinition.objects.get(id='alert')
        
        # Remove fields from schema
        if 'fields' in alert.schema:
            alert.schema['fields'] = [
                f for f in alert.schema['fields'] 
                if f.get('name') not in ['style', 'orientation']
            ]
        
        # Remove from default_params
        if 'style' in alert.default_params:
            del alert.default_params['style']
        if 'orientation' in alert.default_params:
            del alert.default_params['orientation']
        
        alert.save()
        
    except BlockDefinition.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0039_fix_accordion_isopen_format'),
    ]

    operations = [
        migrations.RunPython(add_alert_style_orientation, reverse_alert_style_orientation),
    ]
