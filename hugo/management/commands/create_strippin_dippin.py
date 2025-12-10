import os
import uuid
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from hugo.models import Website, Page, BlockInstance, UploadedFile

class Command(BaseCommand):
    help = 'Create the Strippin Dippin Chicken website with Yelp/FTL data'

    def handle(self, *args, **options):
        # 1. Define Data (From Yelp and Food Truck League)
        site_name = "Strippin Dippin Chicken"
        slug = "strippin-dippin-chicken"
        
        # Extracted Data
        bio = "Jerremy and Ashley started their food truck journey in fall 2021. Fresh chicken tenders and fresh-cut fries (cut right on the truck) with all house-made sauces!"
        tagline = "Fresh Chicken Strips, Hand-Cut Fries & House-Made Sauces"
        address = "West Jordan, UT Area (Mobile Food Truck)"
        hours = "Follow us on Instagram for daily location and hours"
        instagram_url = "https://www.instagram.com/strippindippinchicken/"
        yelp_url = "https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan"
        
        # Colors (Warm, inviting food truck style)
        custom_css = """
:root {
    --color-primary: #DC2626; /* Bold red */
    --color-primary-dark: #B91C1C;
    --color-secondary: #F59E0B; /* Golden yellow */
    --color-accent: #EA580C; /* Orange */
    --color-text: #1F2937;
    --color-bg: #FFFBEB;
    
    --font-heading: 'Poppins', sans-serif;
    --font-body: 'Inter', sans-serif;
}
body {
    background-color: var(--color-bg);
    color: var(--color-text);
}
"""

        # 2. Create Website
        website, created = Website.objects.get_or_create(
            slug=slug,
            defaults={'name': site_name}
        )
        website.custom_css = custom_css
        website.save()
        self.stdout.write(f"Website '{site_name}' ready.")

        # 3. Clear existing pages to rebuild
        website.pages.all().delete()

        # --- HOME PAGE ---
        home_page = Page.objects.create(
            website=website,
            title="Home",
            slug="/",
            status='published'
        )

        # Global Header
        h_row = BlockInstance.objects.create(
            page=home_page,
            definition_id="row",
            placement_key="header",
            sort_order=0,
            params={"gap": "4", "justify": "space-between", "align": "center"}
        )
        BlockInstance.objects.create(
            page=home_page,
            parent=h_row,
            definition_id="brand_logo",
            placement_key="column", 
            sort_order=0,
            params={"brand_name": "Strippin Dippin Chicken", "logo_image": "", "link_url": "/"}
        )
        BlockInstance.objects.create(
            page=home_page,
            parent=h_row,
            definition_id="menu",
            placement_key="column",
            sort_order=1,
            params={
                "style": "pills",
                "responsive": True,
                "items": [
                    {"label": "Home", "url": "/", "type": "link"},
                    {"label": "Menu", "url": "/menu", "type": "link"},
                    {"label": "Find Us", "url": "/#location", "type": "link"}
                ]
            }
        )

        # Main Content
        # Hero
        BlockInstance.objects.create(
            page=home_page,
            definition_id="hero",
            placement_key="main",
            sort_order=0,
            params={
                "title": tagline,
                "subtitle": "Made fresh to order - Watch us cut the fries and batter the chicken right in front of you!",
                "bgImage": "",
                "cta_text": "Find Us Today",
                "cta_url": "#location"
            }
        )

        # About Text
        BlockInstance.objects.create(
            page=home_page,
            definition_id="text",
            placement_key="main",
            sort_order=1,
            params={
                "content": f"""<div class="container mx-auto py-12 px-4 text-center max-w-4xl">
                    <h2 class="text-3xl font-bold mb-6 text-gray-800">Welcome to Strippin Dippin Chicken</h2>
                    <p class="text-lg text-gray-600 leading-relaxed mb-6">
                        {bio} After owning a fencing business for 5 years, we decided to pursue Jerremy's dream of serving great food.
                    </p>
                    <p class="text-lg text-gray-600 leading-relaxed">
                        We developed our chicken and fries concept to ensure the freshest chicken tenders and fresh-cut potatoes - cut right on the truck for each order. All our sauces are Jerremy's own recipes, including our famous black peppercorn ranch!
                    </p>
                </div>"""
            }
        )

        # Features
        BlockInstance.objects.create(
            page=home_page,
            definition_id="features_grid",
            placement_key="main",
            sort_order=2,
            params={
                "title": "Why Choose Us",
                "columns": "3",
                "features": [
                    {"icon": "chef-hat", "title": "Fresh & Made to Order", "description": "We prepare every order fresh - cutting potatoes and battering chicken right on the truck."},
                    {"icon": "utensils", "title": "Hand-Cut Fries", "description": "Our fries are cut fresh from whole potatoes for each order, perfectly salted and crispy."},
                    {"icon": "droplet", "title": "House-Made Sauces", "description": "All our sauces are Jerremy's own recipes, including our famous black peppercorn ranch."}
                ]
            }
        )

        # Reviews Section Title
        BlockInstance.objects.create(
            page=home_page,
            definition_id="text",
            placement_key="main",
            sort_order=3,
            params={
                "content": '<div class="text-center py-8"><h2 class="text-3xl font-bold">What Our Customers Say</h2></div>'
            }
        )

        # Reviews Carousel
        reviews_data = [
            {"name": "James O.", "text": "Great food!! Great price, Awesome value!! Will even cater for your events. No better chicken!!", "rating": 5},
            {"name": "Oscar Z.", "text": "These guys came to my office with a great lunch meal. The hand cut potatoes and the size of the strips left me fully satisfied. The quality of the food showed the care with which it was cooked.", "rating": 5},
            {"name": "Luna D.", "text": "The fries were perfectly salted, the chicken was crispy, and the sauces were amazing. The bbq and peppercorn ranch mix was amazing!", "rating": 5},
            {"name": "John C.", "text": "This food truck was amazing! They make everything from scratch per order. They cut the potatoes and fry the chicken right in front of you. This puts the food truck for chicken at a new level.", "rating": 5},
            {"name": "Keisha F.", "text": "First things first, the ranch is amazing. The black peppercorn ranch is phenomenal! All in all, the flavors are on point and the fact that it's all made to order is really awesome!", "rating": 4}
        ]

        carousel_slides = []
        for review in reviews_data:
            carousel_slides.append({
                "id": str(uuid.uuid4()),
                "children": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "google_reviews",
                        "params": {
                            "show_rating": True,
                            "columns": 1,
                            "reviews": [{
                                "name": review["name"],
                                "rating": review["rating"],
                                "text": review["text"],
                                "date": "Recent",
                                "image": "" 
                            }]
                        }
                    }
                ]
            })

        BlockInstance.objects.create(
            page=home_page,
            definition_id="carousel",
            placement_key="main",
            sort_order=4,
            params={
                "auto_advance": True,
                "interval_seconds": 6,
                "show_dots": True,
                "show_arrows": True,
                "slides": carousel_slides
            }
        )

        # Menu Preview
        BlockInstance.objects.create(
            page=home_page,
            definition_id="menu_grid",
            placement_key="main",
            sort_order=5,
            params={
                "title": "Our Menu",
                "items": [
                    {"name": "2-Piece Chicken Tender Meal", "image": "", "description": "Two fresh chicken tenders with hand-cut fries and your choice of sauce"},
                    {"name": "3-Piece Chicken Tender Meal", "image": "", "description": "Three fresh chicken tenders with hand-cut fries and your choice of sauce"},
                    {"name": "Chicken Salad", "image": "", "description": "Fresh lettuce with crispy chicken, veggies, and your choice of dressing"}
                ]
            }
        )

        # Location
        BlockInstance.objects.create(
            page=home_page,
            definition_id="text",
            placement_key="main",
            sort_order=6,
            params={
                "content": f"""<div id="location" class="bg-gray-100 py-12 text-center">
                    <h2 class="text-3xl font-bold mb-4">Find Us</h2>
                    <p class="text-xl font-semibold mb-2">Mobile Food Truck</p>
                    <p class="text-lg text-gray-700">{address}</p>
                    <p class="text-lg text-gray-700 mt-2">{hours}</p>
                    <div class="mt-6">
                        <a href="{instagram_url}" target="_blank" class="text-blue-600 hover:text-blue-800 underline">Follow us on Instagram</a>
                    </div>
                </div>"""
            }
        )

        # Footer
        BlockInstance.objects.create(
            page=home_page,
            definition_id="text",
            placement_key="footer",
            sort_order=0,
            params={
                "content": f"<p><strong>Strippin Dippin Chicken</strong><br>{address}<br>{hours}</p>"
            }
        )
        BlockInstance.objects.create(
            page=home_page,
            definition_id="social_links",
            placement_key="footer",
            sort_order=1,
            params={
                "links": [
                    {"platform": "instagram", "url": instagram_url},
                    {"platform": "yelp", "url": yelp_url}
                ]
            }
        )

        # --- MENU PAGE ---
        menu_page = Page.objects.create(
            website=website,
            title="Menu",
            slug="/menu",
            status='published'
        )
        
        # Header (Duplicate)
        h_row2 = BlockInstance.objects.create(
            page=menu_page, definition_id="row", placement_key="header", sort_order=0,
            params={"gap": "4", "justify": "space-between", "align": "center"}
        )
        BlockInstance.objects.create(page=menu_page, parent=h_row2, definition_id="brand_logo", placement_key="column", sort_order=0,
                                    params={"brand_name": "Strippin Dippin Chicken", "logo_image": "", "link_url": "/"})
        BlockInstance.objects.create(page=menu_page, parent=h_row2, definition_id="menu", placement_key="column", sort_order=1,
                                    params={"style": "pills", "responsive": True, "items": [{"label": "Home", "url": "/", "type": "link"}, {"label": "Menu", "url": "/menu", "type": "link"}, {"label": "Find Us", "url": "/#location", "type": "link"}]})

        # Menu Page Content
        BlockInstance.objects.create(
            page=menu_page,
            definition_id="hero",
            placement_key="main",
            sort_order=0,
            params={
                "title": "Our Full Menu",
                "subtitle": "Fresh chicken tenders, hand-cut fries, and house-made sauces",
                "bgImage": "",
                "cta_text": "",
                "cta_url": ""
            }
        )
        
        BlockInstance.objects.create(
            page=menu_page,
            definition_id="menu_grid",
            placement_key="main",
            sort_order=1,
            params={
                "title": "Meals",
                "items": [
                    {"name": "2-Piece Chicken Tender Meal", "image": "", "description": "Two fresh chicken tenders with hand-cut fries and your choice of sauce"},
                    {"name": "3-Piece Chicken Tender Meal", "image": "", "description": "Three fresh chicken tenders with hand-cut fries and your choice of sauce"},
                    {"name": "Chicken Salad", "image": "", "description": "Fresh lettuce with crispy chicken tenders, veggies, and your choice of dressing"},
                    {"name": "Hand-Cut Fries", "image": "", "description": "Freshly cut potatoes fried to perfection"},
                ]
            }
        )

        # Sauces Section
        BlockInstance.objects.create(
            page=menu_page,
            definition_id="text",
            placement_key="main",
            sort_order=2,
            params={
                "content": """<div class="container mx-auto py-8 px-4">
                    <h2 class="text-2xl font-bold mb-4 text-center">House-Made Sauces</h2>
                    <p class="text-center text-gray-600 mb-6">All sauces are Jerremy's own recipes!</p>
                    <ul class="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
                        <li class="text-center p-4 bg-gray-50 rounded">Black Peppercorn Ranch ⭐</li>
                        <li class="text-center p-4 bg-gray-50 rounded">BBQ Sauce</li>
                        <li class="text-center p-4 bg-gray-50 rounded">Honey Mustard</li>
                    </ul>
                </div>"""
            }
        )

        # Footer (Duplicate)
        BlockInstance.objects.create(page=menu_page, definition_id="text", placement_key="footer", sort_order=0, params={"content": f"<p><strong>Strippin Dippin Chicken</strong><br>{address}<br>{hours}</p>"})
        BlockInstance.objects.create(page=menu_page, definition_id="social_links", placement_key="footer", sort_order=1, params={"links": [{"platform": "instagram", "url": instagram_url}, {"platform": "yelp", "url": yelp_url}]})

        self.stdout.write(self.style.SUCCESS(f'Successfully created {site_name} site with real content and Yelp reviews!'))
        self.stdout.write(f'Website ID: {website.id}')
        self.stdout.write(f'Pages: {website.pages.count()}')
        self.stdout.write(f'Blocks: {BlockInstance.objects.filter(page__website=website).count()}')
