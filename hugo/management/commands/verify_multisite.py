from django.core.management.base import BaseCommand
from django.test import Client
from hugo.models import Website, Page
import json

class Command(BaseCommand):
    help = 'Verify multi-site functionality'

    def handle(self, *args, **options):
        client = Client()

        # 1. Verify Default Site exists
        try:
            default_site = Website.objects.get(slug='default')
            self.stdout.write(self.style.SUCCESS(f"Default site exists: {default_site.name}"))
        except Website.DoesNotExist:
            self.stdout.write(self.style.ERROR("ERROR: Default site does not exist!"))
            return

        # 2. Create New Website via API
        response = client.post('/api/websites/', {'name': 'Test Site', 'slug': 'test-site'}, content_type='application/json')
        if response.status_code != 201:
            self.stdout.write(self.style.ERROR(f"Failed to create website: {response.status_code}"))
            self.stdout.write(response.content.decode('utf-8')[:1000])
            return
        
        test_site_id = response.json()['id']
        self.stdout.write(self.style.SUCCESS(f"Created Test Site: {test_site_id}"))

        # 3. Create Page on Test Site
        response = client.post('/api/pages/', {
            'title': 'Test Page',
            'slug': '/test-page',
            'website': test_site_id
        }, content_type='application/json')
        
        if response.status_code != 201:
            self.stdout.write(self.style.ERROR(f"Failed to create page: {response.content}"))
            return

        page_id = response.json()['id']
        self.stdout.write(self.style.SUCCESS(f"Created Page on Test Site: {page_id}"))

        # 4. Verify Page is NOT in Default Site list
        response = client.get(f'/api/pages/?website_id={default_site.id}')
        pages = response.json()
        if any(p['id'] == page_id for p in pages):
            self.stdout.write(self.style.ERROR("ERROR: Page found in Default Site list!"))
        else:
            self.stdout.write(self.style.SUCCESS("SUCCESS: Page not found in Default Site list"))

        # 5. Verify Page IS in Test Site list
        response = client.get(f'/api/pages/?website_id={test_site_id}')
        pages = response.json()
        if any(p['id'] == page_id for p in pages):
            self.stdout.write(self.style.SUCCESS("SUCCESS: Page found in Test Site list"))
        else:
            self.stdout.write(self.style.ERROR("ERROR: Page not found in Test Site list!"))

        # 6. Publish Test Site
        response = client.post('/api/pages/publish/', {'website_id': test_site_id}, content_type='application/json')
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS("SUCCESS: Published Test Site"))
            output_dir = response.json().get('output_dir')
            self.stdout.write(f"Output Dir: {output_dir}")
            if 'test-site' in output_dir:
                 self.stdout.write(self.style.SUCCESS("SUCCESS: Output directory contains slug"))
            else:
                 self.stdout.write(self.style.ERROR("ERROR: Output directory does not contain slug"))
        else:
            self.stdout.write(self.style.ERROR(f"ERROR: Publish failed: {response.content}"))
