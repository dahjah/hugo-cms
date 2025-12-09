import os
import django
import sys
from pathlib import Path

# Setup Django environment
sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website
from hugo.views import WebsiteViewSet
from rest_framework.test import APIRequestFactory

def publish_site(slug):
    try:
        website = Website.objects.get(slug=slug)
        print(f"Found website: {website.name} ({website.id})")
        
        factory = APIRequestFactory()
        request = factory.post('/api/websites/publish/', {'website_id': website.id}, format='json')
        
        view = WebsiteViewSet.as_view({'post': 'publish'})
        response = view(request)
        
        print(f"Publish status: {response.status_code}")
        # print(f"Response: {response.data}")
        print("Publish completed.")
        
    except Website.DoesNotExist:
        print(f"Website with slug '{slug}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    publish_site('cairnscounselingcenterv2')
