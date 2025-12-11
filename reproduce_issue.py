
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hugo_cms.settings')
django.setup()

from hugo.scrapers.yelp import YelpScraper, CRAWLEE_AVAILABLE

def test_yelp_scraper():
    print(f"CRAWLEE_AVAILABLE: {CRAWLEE_AVAILABLE}")
    
    url = "https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan"
    print(f"Scraping {url}...")
    
    try:
        # Create context manually to debug connection phase too
        ctx = YelpScraper.connect(url)
        if not ctx.is_valid:
            print(f"Invalid context: {ctx.error}")
            return

        print(f"Context Normalized ID: {ctx.normalized_id}")
        print(f"Menu URL: {ctx.metadata.get('menu_url')}")
        
        profile = YelpScraper.scrape(ctx)
        print(f"Scrape completed.")
        print(f"Name: {profile.name}")
        print(f"Menu Items Count: {len(profile.menu_items)}")
        for item in profile.menu_items:
            print(f" - {item.name}: {item.price}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yelp_scraper()
