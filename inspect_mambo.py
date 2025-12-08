import os
import django
import sys

# Setup Django environment
sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import BlockInstance, BlockDefinition
from django.conf import settings

def inspect_params():
    print(f"Using database: {settings.DATABASES['default']['NAME']}")
    
    print("\nBlock Definitions:")
    for b in BlockDefinition.objects.filter(id='cta_hero'):
        print(f"- {b.id}: {b.label}")
        print(f"  Default Params Keys: {list(b.default_params.keys())}")
        
    print("\nBlock Instances by Type:")
    from django.db.models import Count
    counts = BlockInstance.objects.values('definition_id').annotate(count=Count('id'))
    for c in counts:
        print(f"- {c['definition_id']}: {c['count']}")

    print("\nInspecting blocks on page 'new-page-1764798547482'...")
    from hugo.models import Page
    try:
        # The slug might have a leading slash
        page = Page.objects.get(slug__contains='new-page-1764798547482')
        print(f"Found page: {page.title} ({page.id})")
        blocks = BlockInstance.objects.filter(page=page)
        for block in blocks:
            print(f"Block {block.id} - Type: {block.definition_id}")
            print(f"Params keys: {list(block.params.keys())}")
    except Page.DoesNotExist:
        print("Page not found!")

if __name__ == '__main__':
    inspect_params()
