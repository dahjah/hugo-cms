from django.core.management.base import BaseCommand
from hugo.models import Website, Page, BlockInstance

class Command(BaseCommand):
    help = 'Migrates existing content to a default website'

    def handle(self, *args, **options):
        # Create default website
        website, created = Website.objects.get_or_create(
            slug='default',
            defaults={'name': 'Default Site'}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created default website: {website.name}'))
        else:
            self.stdout.write(f'Using existing website: {website.name}')

        # Assign pages
        pages_count = Page.objects.filter(website__isnull=True).update(website=website)
        self.stdout.write(self.style.SUCCESS(f'Assigned {pages_count} pages to default website'))

        # Assign blocks
        blocks_count = BlockInstance.objects.filter(website__isnull=True).update(website=website)
        self.stdout.write(self.style.SUCCESS(f'Assigned {blocks_count} blocks to default website'))
