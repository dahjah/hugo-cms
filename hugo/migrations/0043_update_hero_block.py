from django.db import migrations

def update_hero_block(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        hero_block = BlockDefinition.objects.get(id='hero')
        
        # Update default params
        hero_block.default_params.update({
            'parallax': False,
            'parallax_strength': 5
        })
        
        # Update schema
        fields = hero_block.schema.get('fields', [])
        
        # Check if fields already exist to avoid duplicates (though schema is JSON, so we just append)
        # We'll just define the new fields structure
        new_fields = [
            {
                'name': 'parallax', 
                'type': 'boolean', 
                'label': 'Parallax scrolling'
            },
            {
                'name': 'parallax_strength', 
                'type': 'range', 
                'label': 'Parallax Strength',
                'min': 1,
                'max': 10,
                'step': 1,
                # Note: The "visible only when checked" logic is frontend-dependent.
                # If the generic form builder supports a 'dependency' key or similar, we'd add it here.
                # For now, we assume simple schema.
            }
        ]
        
        # Append new fields if they are not already there
        existing_names = [f['name'] for f in fields]
        for nf in new_fields:
            if nf['name'] not in existing_names:
                fields.append(nf)
        
        hero_block.schema['fields'] = fields
        hero_block.save()
        
    except BlockDefinition.DoesNotExist:
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('hugo', '0042_convert_stats_menu_schemas'), 
    ]

    operations = [
        migrations.RunPython(update_hero_block),
    ]
