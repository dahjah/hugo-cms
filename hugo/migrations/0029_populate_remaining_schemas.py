from django.db import migrations

def populate_schemas(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    # Helper to update block
    def update_block(id, schema):
        try:
            block = BlockDefinition.objects.get(id=id)
            block.schema = schema
            block.save()
        except BlockDefinition.DoesNotExist:
            pass

    # Hero (Re-applying to ensure consistency)
    update_block('hero', {
        "type": "object",
        "properties": {
            "title": {"type": "string", "label": "Title"},
            "subtitle": {"type": "string", "label": "Subtitle"},
            "bgImage": {"type": "string", "format": "uri", "label": "Background Image"}
        }
    })

    # Text
    update_block('text', {
        "type": "object",
        "properties": {
            "content": {"type": "rich_text", "label": "Content"}
        }
    })

    # Image
    update_block('image', {
        "type": "object",
        "properties": {
            "src": {"type": "string", "format": "uri", "label": "Image Source"},
            "caption": {"type": "string", "label": "Caption"}
        }
    })

    # Markdown
    update_block('markdown', {
        "type": "object",
        "properties": {
            "md": {"type": "text", "label": "Markdown Content"}
        }
    })

    # YouTube
    update_block('youtube', {
        "type": "object",
        "properties": {
            "videoId": {"type": "string", "label": "Video ID"},
            "title": {"type": "string", "label": "Video Title"}
        }
    })

    # Alert
    update_block('alert', {
        "type": "object",
        "properties": {
            "type": {
                "type": "string", 
                "enum": ["info", "success", "warning", "error"],
                "label": "Alert Type"
            },
            "message": {"type": "text", "label": "Message"}
        }
    })

    # Quote
    update_block('quote', {
        "type": "object",
        "properties": {
            "text": {"type": "text", "label": "Quote Text"},
            "author": {"type": "string", "label": "Author"}
        }
    })

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0028_populate_missing_schemas'),
    ]

    operations = [
        migrations.RunPython(populate_schemas),
    ]
