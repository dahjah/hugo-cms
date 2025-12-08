from django.db import migrations

def populate_schemas(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    def update_block(id, schema):
        try:
            block = BlockDefinition.objects.get(id=id)
            block.schema = schema
            block.save()
        except BlockDefinition.DoesNotExist:
            pass

    # Carousel
    update_block('carousel', {
        "type": "object",
        "properties": {
            "auto_advance": {"type": "boolean", "label": "Auto Advance", "default": True},
            "interval_seconds": {"type": "number", "label": "Interval (seconds)", "default": 8, "min": 1, "max": 30},
            "show_dots": {"type": "boolean", "label": "Show Dots", "default": True},
            "show_arrows": {"type": "boolean", "label": "Show Arrows", "default": True},
            "slides": {
                "type": "array",
                "label": "Slides",
                "items": {
                    "type": "object",
                    "properties": {
                        "image": {"type": "string", "format": "uri", "label": "Image"},
                        "title": {"type": "string", "label": "Title"},
                        "description": {"type": "text", "label": "Description"},
                        "cta_text": {"type": "string", "label": "CTA Text"},
                        "cta_url": {"type": "string", "label": "CTA URL"}
                    }
                }
            }
        }
    })

    # Testimonial
    update_block('testimonial', {
        "type": "object",
        "properties": {
            "quote": {"type": "text", "label": "Quote"},
            "author": {"type": "string", "label": "Author"},
            "author_title": {"type": "string", "label": "Author Title"},
            "image": {"type": "string", "format": "uri", "label": "Author Image"}
        }
    })

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0030_populate_cairns_schemas'),
    ]

    operations = [
        migrations.RunPython(populate_schemas),
    ]
