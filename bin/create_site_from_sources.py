#!/usr/bin/env python3
"""
Create Website from Scraper Sources
Usage:
    python bin/create_site_from_sources.py \
        --yelp "the-salty-pineapple-herriman-2" \
        --ftl "https://foodtruckleague.com/Utah/trucks/677ec632f7fd49c21152b236" \
        --instagram "strippindippinchicken" \
        --slug "salty-pineapple"
"""
import os
import sys
import json
import argparse
import requests
import django
from typing import Dict, Any, List
from pathlib import Path

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website, Page, BlockInstance
from hugo.template_service import create_website_from_template
from hugo.utils.yelp_scraper import scrape_yelp_business
from hugo.utils.foodtruckleague_scraper import scrape_food_truck
from hugo.utils.hikerapi_scraper import scrape_instagram_profile_hikerapi
from hugo.utils.extract_design_tokens import run_dembrandt, tokens_to_base_css
from hugo.utils.image_colors import extract_colors_from_path, extract_colors_from_url

class SiteBuilder:
    def __init__(self, slug, name=None):
        self.slug = slug
        self.name = name or slug.replace('-', ' ').title()
        self.data = {
            'yelp': {},
            'ftl': {},
            'instagram': {},
            'colors': ''
        }
        self.website = None
        self.hero_image_local_path = None
        self.media_rel_path = f"uploads/{self.slug}"
        self._ensure_media_dir()

    def _ensure_media_dir(self):
        """Ensure media directory exists"""
        # Assuming typical Django media root structure in project root/media
        # Adjust BASE_DIR usage if needed
        self.media_root = os.path.join(BASE_DIR, 'media', self.media_rel_path)
        os.makedirs(self.media_root, exist_ok=True)

    def _download_image(self, url, filename_prefix="brand"):
        """Download image to media dir and return local path and relative URL"""
        try:
            ext = url.split('.')[-1].split('?')[0]
            if len(ext) > 4: ext = 'jpg'
            
            filename = f"{filename_prefix}.{ext}"
            local_path = os.path.join(self.media_root, filename)
            
            # Simple caching: don't re-download if exists
            if not os.path.exists(local_path):
                print(f"Downloading {url} to {local_path}...")
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                else:
                    return None, None
            else:
                print(f"Using cached image: {local_path}")
            
            # Return full local path (for colorgram) and relative path (for CMS)
            rel_path = f"/media/{self.media_rel_path}/{filename}"
            return local_path, rel_path
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None, None

    def fetch_data(self, yelp_slug=None, ftl_url=None, ig_user=None):
        """Run all scrapers"""
        if yelp_slug:
            print(f"Scraping Yelp: {yelp_slug}...")
            self.data['yelp'] = scrape_yelp_business(yelp_slug)
            
        if ftl_url:
            print(f"Scraping FTL: {ftl_url}...")
            ftl_json = scrape_food_truck(ftl_url)
            self.data['ftl'] = json.loads(ftl_json)
            
        if ig_user:
            print(f"Scraping Instagram: {ig_user}...")
            ig_json = scrape_instagram_profile_hikerapi(ig_user)
            self.data['instagram'] = json.loads(ig_json)

    def generate_colors(self):
        """Generate color palette using Plan A (Website) or Plan B (Image)"""
        # Try external URL from IG or Yelp
        website_url = self.data['instagram'].get('external_url') or self.data['ftl'].get('book_link')
        
        # Filter out generic links
        if website_url and ('linktr.ee' in website_url or 'yelp.com' in website_url):
            website_url = None

        if website_url:
            print(f"Generating colors from website: {website_url}...")
            tokens = run_dembrandt(website_url)
            if tokens:
                self.data['colors'] = tokens_to_base_css(tokens)
                return

        # Fallback: Image extraction
        print("Using image-based color extraction...")
        # Prioritize: Logo > Yelp Hero > Profile Pic
        image_url = None
        if self.data['yelp'].get('photos'):
            image_url = self.data['yelp']['photos'][0]
        elif self.data['instagram'].get('profile_pic_url'):
            image_url = self.data['instagram']['profile_pic_url']
            
        if image_url:
            # Download image first used locally and for CMS
            local_path, rel_path = self._download_image(image_url, "brand_hero")
            
            if local_path:
                print(f"Extracting colors from local image: {local_path}")
                self.data['colors'] = extract_colors_from_path(local_path)
                self.hero_image_local_path = rel_path # Store for _populate_hero

    def create_site(self):
        """Create and populate the site"""
        print(f"Creating website: {self.name} ({self.slug})...")
        self.website = create_website_from_template(
            template_slug="food-truck-v2",
            website_name=self.name,
            website_slug=self.slug
        )
        
        # Apply Colors
        if self.data['colors']:
            self.website.base_css = self.data['colors']
            self.website.save()
            print("✓ Applied color theme")

        self._populate_hero()
        self._populate_story()
        self._populate_menu()
        self._populate_reviews()
        self._populate_footer()
        self._populate_social()
        
    def _populate_hero(self):
        home = Page.objects.get(website=self.website, slug='/')
        hero = BlockInstance.objects.filter(page=home, definition_id='hero').first()
        if not hero: return

        # Name: Yelp > FTL > Slug
        name = self.data['yelp'].get('name') or self.data['ftl'].get('name') or self.name
        
        # Subheadline: FTL Subtitle > IG Bio
        sub = self.data['ftl'].get('subtitle') or self.data['instagram'].get('biography', '')[:100]
        
        # Image: Yelp High Res > IG Post
        img = ''
        if self.hero_image_local_path:
            img = self.hero_image_local_path
        elif self.data['yelp'].get('photos'):
            img = self.data['yelp']['photos'][0]
        elif self.data['instagram'].get('posts'):
             img = self.data['instagram']['posts'][0].get('image_url')

        hero.params.update({
            'headline': name,
            'subheadline': sub,
            'image': img,
            'cta_text': 'View Menu',
            'cta_link': '/menu'
        })
        hero.save()
        print("✓ Populated Hero")

    def _populate_story(self):
        home = Page.objects.get(website=self.website, slug='/')
        story = BlockInstance.objects.filter(page=home, definition_id='text').first()
        if not story: return

        # Content: FTL Bio (Rich) > IG Bio
        content = self.data['ftl'].get('bio')
        if not content or content == 'N/A':
            content = self.data['instagram'].get('biography')
            
        if content:
            story.params['content'] = f"<h2>Our Story</h2><p>{content}</p>"
            story.save()
            print("✓ Populated Story")

    def _populate_menu(self):
        menu_page = Page.objects.get(website=self.website, slug='/menu')
        grid = BlockInstance.objects.filter(page=menu_page, definition_id='menu_grid').first()
        if not grid: return

        items = self.data['yelp'].get('menu_items', [])
        if items:
            # Map Yelp format to Block format
            mapped = []
            for item in items:
                mapped.append({
                    'name': item.get('name'),
                    'description': item.get('description', ''),
                    'price': item.get('price', ''),
                    'image': '' # Yelp menu scraping doesn't get images yet
                })
            grid.params['items'] = mapped
            grid.save()
            print(f"✓ Populated Menu ({len(items)} items)")

    def _populate_reviews(self):
        # Yelp scraper currently doesn't fetch reviews text (only rating count)
        # Placeholder for future expansion
        pass

    def _populate_footer(self):
        footer = BlockInstance.objects.filter(website=self.website, placement_key='footer').first()
        if not footer: return

        loc = self.data['yelp'].get('location', '')
        phone = self.data['yelp'].get('phone', '')
        if isinstance(phone, dict): phone = phone.get('formatted', '')
        
        email = self.data['instagram'].get('business_email', '') # HikerAPI might have this

        content = f"<p><strong>{self.name}</strong><br>"
        if loc: content += f"{loc}<br>"
        if phone: content += f"{phone}<br>"
        content += "Follow us for daily updates!</p>"

        footer.params['content'] = content
        footer.save()
        print("✓ Populated Footer")

    def _populate_social(self):
        social = BlockInstance.objects.filter(website=self.website, definition_id='social_links').first()
        if not social: return

        links = []
        if self.data['instagram'].get('username'):
            links.append({'platform': 'instagram', 'url': f"https://instagram.com/{self.data['instagram']['username']}"})
        
        # FTL link is usually passed as arg, store it?
        
        if self.data['yelp'].get('menu_url'):
             # Yelp Biz URL is menu_url base
             base = self.data['yelp']['menu_url'].replace('/menu/', '/biz/')
             links.append({'platform': 'yelp', 'url': base})

        social.params['links'] = links
        social.save()
        print("✓ Populated Social Links")


def main():
    parser = argparse.ArgumentParser(description="Create site from sources")
    parser.add_argument("--slug", required=True, help="Website slug")
    parser.add_argument("--name", help="Website name")
    parser.add_argument("--yelp", help="Yelp business slug")
    parser.add_argument("--ftl", help="Food Truck League URL")
    parser.add_argument("--instagram", help="Instagram username")
    
    args = parser.parse_args()
    
    builder = SiteBuilder(args.slug, args.name)
    builder.fetch_data(args.yelp, args.ftl, args.instagram)
    builder.generate_colors()
    builder.create_site()
    
    print(f"\n✅ Site Created: http://localhost:8000/cms/website/{builder.website.id}/")

if __name__ == '__main__':
    main()
