from django.db import migrations

def add_menu_position_params(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    try:
        menu = BlockDefinition.objects.get(id='menu')
        
        # Add position and opacity fields to schema if not present
        fields = menu.schema.get('fields', [])
        
        # Check if already present to avoid duplicates
        has_position = any(f['name'] == 'position' for f in fields)
        has_opacity = any(f['name'] == 'opacity' for f in fields)
        
        if not has_position:
            fields.append({
                'name': 'position',
                'type': 'select',
                'label': 'Position',
                'options': ['inline', 'sticky', 'overlayed']
            })
            
        if not has_opacity:
            fields.append({
                'name': 'opacity',
                'type': 'number',
                'label': 'Background Opacity (0-100)',
                'default': 100
            })
            
        menu.schema['fields'] = fields
        
        # Update default params
        if 'position' not in menu.default_params:
            menu.default_params['position'] = 'inline'
        if 'opacity' not in menu.default_params:
            menu.default_params['opacity'] = 100
            
        menu.save()
    except BlockDefinition.DoesNotExist:
        pass

def reverse_menu_params(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    try:
        menu = BlockDefinition.objects.get(id='menu')
        fields = menu.schema.get('fields', [])
        menu.schema['fields'] = [f for f in fields if f['name'] not in ['position', 'opacity']]
        
        if 'position' in menu.default_params:
            del menu.default_params['position']
        if 'opacity' in menu.default_params:
            del menu.default_params['opacity']
            
        menu.save()
    except BlockDefinition.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0046_page_sort_order_alter_website_theme_preset'),
    ]


    operations = [
        migrations.RunPython(add_menu_position_params, reverse_menu_params),
    ]
