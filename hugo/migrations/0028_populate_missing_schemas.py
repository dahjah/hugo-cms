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

    # CTA Hero
    update_block('cta_hero', {
        "type": "object",
        "properties": {
            "headline": {"type": "string"},
            "subheadline": {"type": "string"},
            "cta_text": {"type": "string"},
            "cta_url": {"type": "string"},
            "background_image": {"type": "string", "format": "uri"}
        }
    })

    # Features Grid
    update_block('features_grid', {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "features": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "icon": {"type": "string", "enum": ["check", "star", "heart", "zap", "shield", "truck"]},
                        "title": {"type": "string"},
                        "description": {"type": "text"}
                    }
                }
            }
        }
    })

    # Process Steps
    update_block('process_steps', {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "text"}
                    }
                }
            }
        }
    })

    # Stats Counter
    update_block('stats_counter', {
        "type": "object",
        "properties": {
            "stats": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "suffix": {"type": "string"},
                        "label": {"type": "string"}
                    }
                }
            }
        }
    })

    # Menu Grid
    update_block('menu_grid', {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "image": {"type": "string", "format": "uri"},
                        "description": {"type": "text"}
                    }
                }
            }
        }
    })

    # Social Links
    update_block('social_links', {
        "type": "object",
        "properties": {
            "links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "enum": ["facebook", "instagram", "twitter", "linkedin", "youtube"]},
                        "url": {"type": "string"}
                    }
                }
            }
        }
    })

    # FAQ
    update_block('faq', {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "text"}
                    }
                }
            }
        }
    })

    # Google Reviews
    update_block('google_reviews', {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "rating": {"type": "number", "min": 1, "max": 5},
                        "text": {"type": "text"},
                        "date": {"type": "string"},
                        "image": {"type": "string", "format": "uri"}
                    }
                }
            }
        }
    })

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0027_update_layout_zones_scope'),
    ]

    operations = [
        migrations.RunPython(populate_schemas),
    ]
