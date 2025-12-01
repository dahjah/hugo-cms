import os
import sys
sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
import django
import json
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hugo_cms.settings")
django.setup()

from hugo.models import Website, Page, BlockInstance

def verify():
    client = Client()

    # 1. Verify Default Site exists
    try:
        default_site = Website.objects.get(slug='default')
        print(f"Default site exists: {default_site.name}")
    except Website.DoesNotExist:
        print("ERROR: Default site does not exist!")
        return

    # 2. Create New Website via API
    response = client.post('/api/websites/', {'name': 'Test Site', 'slug': 'test-site'}, content_type='application/json')
    if response.status_code != 201:
        print(f"Failed to create website: {response.content}")
        return
    
    test_site_id = response.json()['id']
    print(f"Created Test Site: {test_site_id}")

    # 3. Create Page on Test Site
    # PageDetailSerializer is used for create
    response = client.post('/api/pages/', {
        'title': 'Test Page',
        'slug': '/test-page',
        'website': test_site_id
    }, content_type='application/json')
    
    if response.status_code != 201:
        print(f"Failed to create page: {response.content}")
        return

    page_id = response.json()['id']
    print(f"Created Page on Test Site: {page_id}")

    # 4. Verify Page is NOT in Default Site list
    response = client.get(f'/api/pages/?website_id={default_site.id}')
    pages = response.json()
    if any(p['id'] == page_id for p in pages):
        print("ERROR: Page found in Default Site list!")
    else:
        print("SUCCESS: Page not found in Default Site list")

    # 5. Verify Page IS in Test Site list
    response = client.get(f'/api/pages/?website_id={test_site_id}')
    pages = response.json()
    if any(p['id'] == page_id for p in pages):
        print("SUCCESS: Page found in Test Site list")
    else:
        print("ERROR: Page not found in Test Site list!")

    # 6. Publish Test Site
    response = client.post('/api/pages/publish/', {'website_id': test_site_id}, content_type='application/json')
    if response.status_code == 200:
        print("SUCCESS: Published Test Site")
        output_dir = response.json().get('output_dir')
        print(f"Output Dir: {output_dir}")
        if 'test-site' in output_dir:
             print("SUCCESS: Output directory contains slug")
        else:
             print("ERROR: Output directory does not contain slug")
    else:
        print(f"ERROR: Publish failed: {response.content}")

if __name__ == '__main__':
    verify()
