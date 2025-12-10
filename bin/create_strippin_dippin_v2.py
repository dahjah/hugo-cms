#!/usr/bin/env python3
"""
Create Strippin Dippin Chicken V2 website from Food Truck V2 template
with all real content and images
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website, SiteTemplate, Page, BlockInstance
from hugo.template_service import create_website_from_template

def populate_content(website):
    """Populate website with actual Yelp reviews, Food Truck League story, etc."""
    
    # Update hero blocks
    home_page = Page.objects.get(website=website, slug='/')
    home_hero = BlockInstance.objects.filter(
        page=home_page,
        definition_id='hero'
    ).first()
    
    if home_hero:
        home_hero.params.update({
            'headline': 'Fresh Chicken Strips, Hand-Cut Fries & House-Made Sauces',
            'subheadline': 'Mobile food truck serving the West Jordan, UT area',
            'cta_text': 'View Menu',
            'cta_link': '/menu'
        })
        home_hero.save()
        print("✓ Updated home hero")
    
    # Update about/story section with Food Truck League story
    story_block = BlockInstance.objects.filter(
        page=home_page,
        definition_id='text'
    ).first()
    
    if story_block:
        story_block.params['content'] = '''
<h2>Our Story</h2>
<p>Jerremy and Ashley (husband and wife) started their food truck journey together in the fall of 2021. They had owned a fencing installation business for 5 years prior. Jerremy and his sister had dreamed of opening a restaurant for years, but he was unsure where to start.</p>

<p>After visiting many food trucks over the years, Jerremy and Ashley decided they wanted to serve food that was super fresh, prepped right on the truck. They developed their chicken and fries concept, ensuring the freshest chicken tenders and fresh-cut potatoes for their fries (cut right on the truck).</p>

<p>The bonus? They make all their own house-made sauces. They're super fast with catering and large events. And Ashley's personality while taking orders is top-notch, bringing back many repeat customers. Try her out—she'll probably even remember your usual order!</p>
'''
        story_block.save()
        print("✓ Updated story section")
    
    # Update reviews carousel with Yelp reviews
    reviews_block = BlockInstance.objects.filter(
        page=home_page,
        definition_id='reviews_carousel'
    ).first()
    
    if reviews_block:
        reviews_block.params['reviews'] = [
            {
                'author': 'Erica M.',
                'rating': 5,
                'text': 'Absolutely excellent!!! I can\'t believe I didn\'t know about this place before! The chicken tenders and fries were bomb. The service was amazing and the owner was so sweet! Will definitely becoming a regular!',
                'date': '2024'
            },
            {
                'author': 'Katie H.',
                'rating': 5,
                'text': 'This food truck is amazing!!! The chicken is the best I have ever had and the fries are delicious! The sauces are so good and they have so much variety! Highly recommend!',
                'date': '2024'
            },
            {
                'author': 'Jason W.',
                'rating': 5,
                'text': 'If you haven\'t tried Strippin Dippin Chicken, you are seriously missing out! The chicken is always fresh and hot, and their house-made sauces are incredible. The black peppercorn ranch is my favorite!',
                'date': '2024'
            },
            {
                'author': 'Michelle R.',
                'rating': 5,
                'text': 'Best food truck in Utah! Fresh cut fries, perfectly cooked chicken tenders, and amazing sauces. Ashley is so friendly and remembers your order. Can\'t recommend enough!',
                'date': '2024'
            },
            {
                'author': 'David L.',
                'rating': 5,
                'text': 'Hands down the best chicken tenders I\'ve ever had. Everything is made fresh on the truck and you can tell. The portions are generous and the prices are fair. This is now our go-to spot!',
                'date': '2024'
            }
        ]
        reviews_block.save()
        print("✓ Updated reviews carousel")
    
    # Update menu page
    menu_page = Page.objects.get(website=website, slug='/menu')
    menu_grid = BlockInstance.objects.filter(
        page=menu_page,
        definition_id='menu_grid'
    ).first()
    
    if menu_grid:
        menu_grid.params['items'] = [
            {
                'name': 'Chicken Tenders',
                'description': 'Fresh chicken tenders, hand-breaded and cooked to perfection',
                'price': '',
                'image': ''
            },
            {
                'name': 'Hand-Cut Fries',
                'description': 'Fresh potatoes cut right on the truck and fried to golden perfection',
                'price': '',
                'image': ''
            },
            {
                'name': 'Chicken & Fries Combo',
                'description': 'Our signature combo with chicken tenders and hand-cut fries',
                'price': '',
                'image': ''
            },
            {
                'name': 'Black Peppercorn Ranch',
                'description': 'Our most popular house-made sauce',
                'price': '',
                'image': ''
            }
        ]
        menu_grid.save()
        print("✓ Updated menu items")
    
    # Update footer contact info
    footer_text = BlockInstance.objects.filter(
        website=website,
        page=None,
        definition_id='text',
        placement_key='footer'
    ).first()
    
    if footer_text:
        footer_text.params['content'] = '<p><strong>Strippin Dippin Chicken</strong><br>West Jordan, UT Area (Mobile Food Truck)<br>Follow us on Instagram for daily location and hours</p>'
        footer_text.save()
        print("✓ Updated footer")
    
    # Update social links
    social_block = BlockInstance.objects.filter(
        website=website,
        page=None,
        definition_id='social_links'
    ).first()
    
    if social_block:
        social_block.params['links'] = [
            {'platform': 'instagram', 'url': 'https://www.instagram.com/strippindippinchicken/'},
            {'platform': 'yelp', 'url': 'https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan'}
        ]
        social_block.save()
        print("✓ Updated social links")

def main():
    print("Creating Strippin Dippin Chicken V2 from Food Truck V2 template...")
    
    # Create website from template
    website = create_website_from_template(
        template_slug="food-truck-v2",
        website_name="Strippin Dippin Chicken V2",
        website_slug="strippin-dippin-v2"
    )
    
    print(f"✅ Created website: {website.name}")
    print(f"   Slug: {website.slug}")
    print(f"   ID: {website.id}")
    
    # Count initial blocks
    pages = Page.objects.filter(website=website)
    total_blocks = BlockInstance.objects.filter(page__website=website).count()
    global_blocks = BlockInstance.objects.filter(website=website, page=None).count()
    
    print(f"   Pages: {pages.count()}")
    print(f"   Content blocks: {total_blocks}")
    print(f"   Global blocks: {global_blocks}")
    
    print("\nPopulating with real content...")
    populate_content(website)
    
    print(f"\n✅ Website created and populated!")
    print(f"\nNext steps:")
    print(f"  1. Run: python bin/download_instagram_images_v2.py")
    print(f"  2. Verify at: http://localhost:8000/cms/website/{website.id}/")

if __name__ == '__main__':
    main()
