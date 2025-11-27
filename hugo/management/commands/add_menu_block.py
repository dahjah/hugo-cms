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
                        {'label': 'Home', 'url': '/', 'type': 'page'},
                        {'label': 'About', 'url': '/about', 'type': 'page'},
                        {'label': 'Contact', 'url': '/contact', 'type': 'page'}
                    ],
                    'orientation': 'horizontal',  # or 'vertical'
                    'alignment': 'left',  # 'left', 'center', 'right'
                    'style': 'default',  # 'default', 'pills', 'underline'
                    'responsive': 'false',  # 'false' = always visible, 'true' = hamburger menu
                    'hamburgerDirection': 'dropdown',  # 'dropdown' = from top, 'sidebar' = from side
                    'sidebarSide': 'left',  # 'left' or 'right' - which side sidebar slides from
                    'sidebarFooterBlocks': []  # Array of blocks for sidebar footer area
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created menu block definition'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated menu block definition'))
