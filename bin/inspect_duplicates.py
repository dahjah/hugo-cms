
import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website, Page

website = Website.objects.get(slug='strippin-v2')
print(f"Website: {website.name}")

home_pages = Page.objects.filter(website=website, slug='/')
print(f"Home Pages count: {home_pages.count()}")

for p in home_pages:
    block_count = p.main_blocks.count()
    print(f"Page ID: {p.id} | Slug: {p.slug} | Blocks: {block_count}")
