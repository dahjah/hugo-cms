from django.core.management.base import BaseCommand
from django.test import Client
from hugo.models import Website, Page

class Command(BaseCommand):
    help = 'Test that Home page is auto-created for new websites'

    def handle(self, *args, **options):
        client = Client()

        # Create a new website
        response = client.post('/api/websites/', {
            'name': 'Auto Home Test',
            'slug': 'auto-home-test'
        }, content_type='application/json')
        
        if response.status_code != 201:
            self.stdout.write(self.style.ERROR(f"Failed to create website: {response.status_code}"))
            return
        
        website_id = response.json()['id']
        self.stdout.write(self.style.SUCCESS(f"Created website: {website_id}"))
        
        # Check if Home page was auto-created
        home_page = Page.objects.filter(website_id=website_id, slug='/').first()
        
        if home_page:
            self.stdout.write(self.style.SUCCESS(f"✓ Home page auto-created!"))
            self.stdout.write(f"  Title: {home_page.title}")
            self.stdout.write(f"  Slug: {home_page.slug}")
            self.stdout.write(f"  Status: {home_page.status}")
        else:
            self.stdout.write(self.style.ERROR("✗ Home page was NOT auto-created"))
