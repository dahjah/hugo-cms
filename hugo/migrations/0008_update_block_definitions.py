from django.db import migrations

def update_block_definitions(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')

    # Update Image Block
    try:
        image_def = BlockDefinition.objects.get(id='image')
        default_params = image_def.default_params
        default_params['width'] = '100%'
        default_params['height'] = 'auto'
        image_def.default_params = default_params
        image_def.save()
    except BlockDefinition.DoesNotExist:
        pass

    # Update YouTube Block
    try:
        youtube_def = BlockDefinition.objects.get(id='youtube')
        default_params = youtube_def.default_params
        default_params['width'] = '100%'
        default_params['aspect_ratio'] = '16/9'
        youtube_def.default_params = default_params
        youtube_def.save()
    except BlockDefinition.DoesNotExist:
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('hugo', '0007_storagesettings_uploadedfile'),
    ]

    operations = [
        migrations.RunPython(update_block_definitions),
    ]
