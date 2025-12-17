"""
Remove style and orientation fields from alert block
"""
from django.db import migrations


def remove_alert_style_orientation(apps, schema_editor):
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


def reverse_remove_alert_style_orientation(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        alert = BlockDefinition.objects.get(id='alert')
        
        # Add fields back to schema
        if 'fields' in alert.schema:
            alert.schema['fields'].extend([
                {
                    'name': 'style',
                    'type': 'select',
                    'label': 'Style',
                    'options': ['normal', 'dash', 'soft'],
                    'default': 'normal'
                },
                {
                    'name': 'orientation',
                    'type': 'select',
                    'label': 'Orientation',
                    'options': ['horizontal', 'vertical'],
                    'default': 'horizontal'
                }
            ])
        
        # Add to default_params
        alert.default_params['style'] = 'normal'
        alert.default_params['orientation'] = 'horizontal'
        
        alert.save()
        
    except BlockDefinition.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0040_add_alert_style_orientation'),
    ]

    operations = [
        migrations.RunPython(remove_alert_style_orientation, reverse_remove_alert_style_orientation),
    ]
