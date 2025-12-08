from django.db import migrations

def update_column_schema(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    try:
        column = BlockDefinition.objects.get(id='column')
        # Add width property to schema
        schema = column.schema
        schema['properties']['width'] = {
            "type": "string", 
            "default": "100%", 
            "description": "Width in % (e.g. 50%, 33.3%)"
        }
        column.schema = schema
        column.save()
    except BlockDefinition.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0025_populate_schemas'),
    ]

    operations = [
        migrations.RunPython(update_column_schema),
    ]
