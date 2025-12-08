from django.db import migrations

def set_carousel_container(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    try:
        carousel = BlockDefinition.objects.get(id='carousel')
        carousel.is_container = True
        carousel.save()
    except BlockDefinition.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0031_populate_carousel_schema'),
    ]

    operations = [
        migrations.RunPython(set_carousel_container),
    ]
