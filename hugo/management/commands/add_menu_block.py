from django.core.management.base import BaseCommand
from hugo.models import BlockDefinition

class Command(BaseCommand):
    help = 'Add menu block definition to the CMS'

    def handle(self, *args, **options):
        menu_block, created = BlockDefinition.objects.update_or_create(
            id='menu',
            defaults={
                'label': 'Navigation Menu',
                'icon': 'menu',
                'has_visual_preview': True,
                'default_params': {
                    'items': [
                        {'label': 'Home', 'url': '/'},
                        {'label': 'About', 'url': '/about'},
                        {'label': 'Contact', 'url': '/contact'}
                    ],
                    'orientation': 'horizontal',  # or 'vertical'
                    'alignment': 'left',  # 'left', 'center', 'right'
                    'style': 'default'  # 'default', 'pills', 'underline'
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created menu block definition'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated menu block definition'))
