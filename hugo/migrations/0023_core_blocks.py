from django.db import migrations

def create_core_blocks(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    # Row Block
    BlockDefinition.objects.create(
        id='row',
        label='Row (Flex/Grid)',
        icon='layout-row',
        default_params={
            'cols': '1', # Default columns on mobile/base
            'md_cols': '2', # Default columns on medium screens
            'gap': '4',
            'class': ''
        }
    )
    
    # Column Block
    BlockDefinition.objects.create(
        id='column',
        label='Column',
        icon='columns',
        default_params={
            'span': '1',
            'class': ''
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0022_add_layout_blocks'),
    ]

    operations = [
        migrations.RunPython(create_core_blocks),
    ]
