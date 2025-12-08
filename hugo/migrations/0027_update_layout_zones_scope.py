from django.db import migrations

def update_layout_zones_scope(apps, schema_editor):
    LayoutTemplate = apps.get_model('hugo', 'LayoutTemplate')
    
    for layout in LayoutTemplate.objects.all():
        updated_zones = []
        for zone in layout.zones:
            # Add scope if missing
            if 'scope' not in zone:
                if zone['name'] in ['header', 'footer']:
                    zone['scope'] = 'global'
                else:
                    zone['scope'] = 'page'
            updated_zones.append(zone)
        
        layout.zones = updated_zones
        layout.save()

class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0026_update_column_schema'),
    ]

    operations = [
        migrations.RunPython(update_layout_zones_scope),
    ]
