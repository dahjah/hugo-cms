from django.db import migrations

def populate_schemas(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    # Helper to update block
    def update_block(id, is_container, schema):
        try:
            block = BlockDefinition.objects.get(id=id)
            block.is_container = is_container
            block.schema = schema
            block.save()
        except BlockDefinition.DoesNotExist:
            pass

    # Section
    update_block('section', True, {
        "type": "object",
        "properties": {
            "style": {"type": "string", "enum": ["default", "primary", "dark"], "default": "default"},
            "class": {"type": "string", "default": ""}
        }
    })
    
    # Row
    update_block('row', True, {
        "type": "object",
        "properties": {
            "cols": {"type": "string", "default": "1"},
            "md_cols": {"type": "string", "default": "2"},
            "gap": {"type": "string", "default": "4"},
            "class": {"type": "string", "default": ""}
        }
    })
    
    # Column
    update_block('column', True, {
        "type": "object",
        "properties": {
            "span": {"type": "string", "default": "1"},
            "class": {"type": "string", "default": ""}
        }
    })
    
    # Hero
    update_block('hero', False, {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "bgImage": {"type": "string", "format": "uri"}
        }
    })

    # HTML
    update_block('html', False, {
        "type": "object",
        "properties": {
            "content": {"type": "string", "format": "html"}
        }
    })

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0024_blockdefinition_is_container_blockdefinition_schema_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_schemas),
    ]
