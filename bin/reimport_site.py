import os
import django
import sys
from pathlib import Path

sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website
from hugo.management.commands.import_hugo_site import Command

def reimport():
    slug = 'cairnscounselingcenterv2'
    
    # Delete existing
    try:
        ws = Website.objects.get(slug=slug)
        print(f"Deleting existing website: {ws.name}")
        ws.delete()
    except Website.DoesNotExist:
        pass
        
    # Import
    print("Importing site...")
    path = '/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms/cairnscounseling'
    cmd = Command()
    # Call the logic directly or via handle if possible, but cleaner to call the importer function if I can import it.
    from hugo.hugo_importer import import_hugo_site
    website = import_hugo_site(path, "Cairns Counseling V2", slug)
    print(f"Imported: {website.name}")

if __name__ == "__main__":
    reimport()
