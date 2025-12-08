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

    # Flip Cards Grid
    # Note: We use a flattened structure for card items to simplify the sidebar editor
    update_block('flip_cards', {
        "type": "object",
        "properties": {
            "columns": {"type": "number", "min": 1, "max": 4, "default": 3, "label": "Columns"},
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "front_title": {"type": "string", "label": "Front Title"},
                        "front_icon": {"type": "string", "label": "Front Icon (Lucide name)"},
                        "back_description": {"type": "text", "label": "Back Description"},
                        "back_cta_text": {"type": "string", "label": "Back CTA Text"},
                        "back_cta_url": {"type": "string", "label": "Back CTA URL"}
                    }
                }
            }
        }
    })

    # Accordion/FAQ
    update_block('accordion', {
        "type": "object",
        "properties": {
            "title": {"type": "string", "label": "Section Title"},
            "allow_multiple": {"type": "boolean", "label": "Allow Multiple Open"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "label": "Question/Title"},
                        "content": {"type": "text", "label": "Answer/Content"}
                    }
                }
            }
        }
    })

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0029_populate_remaining_schemas'),
    ]

    operations = [
        migrations.RunPython(populate_schemas),
    ]
