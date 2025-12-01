from django.core.management.base import BaseCommand
from hugo.models import BlockDefinition

class Command(BaseCommand):
    help = 'Add HTML block definition to the CMS'

    def handle(self, *args, **options):
        html_block, created = BlockDefinition.objects.update_or_create(
            id='html',
            defaults={
                'label': 'HTML Block',
                'icon': 'code',
                'has_visual_preview': True,
                'default_params': {
                    'html': '<div class="p-4">\n  <h3>Custom HTML</h3>\n  <p>Add your HTML here.</p>\n</div>'
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created HTML block definition'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated HTML block definition'))
