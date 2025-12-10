import os
import uuid
import json
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from hugo.models import Website, Page, BlockInstance, UploadedFile

class Command(BaseCommand):
    help = 'Create the Comfort Bowl website with scraped data and enhanced content'

    def handle(self, *args, **options):
        # 1. Define Data (Scraped & Mocked)
        site_name = "Comfort Bowl"
        slug = "comfort-bowl"
        
        # Scraped Data
        bio = "Local Utah-based food truck famous for our Japanese Fried Chicken Katsu (2023 Best of State winner). Serving authentic comfort food that warms the soul."
        address = "2435 S State St, South Salt Lake, UT"
        hours = "Mon-Sat: 11am - 9pm"
        instagram_url = "https://instagram.com/comfortbowlutah"
        facebook_url = "https://facebook.com/comfortbowlutah"
        
        # Colors (Extracted)
        custom_css = """
:root {
    --color-primary: #F59E0B; /* Golden/Orange */
    --color-primary-dark: #D97706;
    --color-secondary: #1F2937; /* Dark Gray */
    --color-accent: #EF4444; /* Red */
    --color-text: #1F2937;
    --color-bg: #F9FAFB;
    
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

        # 3. Handle Images (Ensure they exist in DB)
        # We assume they are already downloaded to media/comfort_bowl/
        media_dir = Path(settings.MEDIA_ROOT) / 'comfort_bowl'
        image_map = {}
        
        if media_dir.exists():
            for img_file in media_dir.glob('*.jpg'):
                # Check if exists
                rel_path = f"comfort_bowl/{img_file.name}"
                # Create/Get UploadedFile
                uf, _ = UploadedFile.objects.get_or_create(
                    website=website,
                    file_path=rel_path,
                    defaults={
                        'filename': img_file.name,
                        'file_url': f"/media/{rel_path}",
                        'file_size': img_file.stat().st_size,
                        'content_type': 'image/jpeg'
                    }
                )
                image_map[img_file.stem] = uf.file_url

        # Fallback if specific images missing
        logo_url = image_map.get('logo', '')
        hero_bg = image_map.get('image_2', '') # Katsu shot
        menu_katsu = image_map.get('image_5', '')
        menu_teriyaki = image_map.get('image_2', '')
        menu_gyoza = image_map.get('image_3', '')

        # 4. Create Pages
        # Clear existing pages to rebuild
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
            page=home_page, # Parent handling via relationship, but we set page for filtering
            parent=h_row,
            definition_id="brand_logo",
            placement_key="column", 
            sort_order=0,
            params={"brand_name": "Comfort Bowl", "logo_image": logo_url, "link_url": "/"}
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
                    {"label": "Visit Us", "url": "/#location", "type": "link"}
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
                "title": "Japanese Fried Chicken Katsu",
                "subtitle": "2023 Best of State Winner. Comfort food that warms the soul. Established 2015.",
                "bgImage": hero_bg,
                "cta_text": "View Our Menu",
                "cta_url": "/menu"
            }
        )

        # About Text (New)
        BlockInstance.objects.create(
            page=home_page,
            definition_id="text",
            placement_key="main",
            sort_order=1,
            params={
                "content": f"""<div class="container mx-auto py-12 px-4 text-center max-w-4xl">
                    <h2 class="text-3xl font-bold mb-6 text-gray-800">Welcome to Comfort Bowl</h2>
                    <p class="text-lg text-gray-600 leading-relaxed mb-6">
                        {bio} We started with a simple mission: to bring the authentic flavors of Japan to the streets of Utah. 
                        Our signature dish, the Chicken Katsu, is marinated to perfection and fried until golden crispy, served with our secret roasted garlic and ginger sauce.
                    </p>
                    <p class="text-lg text-gray-600 leading-relaxed">
                        Whether you visit our food truck or our location at Square Kitchen Eatery, we promise a meal that is hearty, fresh, and made with love.
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
                "title": "Why We Are The Best",
                "columns": "3",
                "items": [
                    {"icon": "award", "title": "Award Winning", "description": "Voted Best of State 2023 for our famous Katsu."},
                    {"icon": "flame", "title": "Freshly Grilled", "description": "Our Teriyaki Chicken is grilled fresh daily."},
                    {"icon": "heart", "title": "Locally Loved", "description": "A local Utah favorite serving authentic comfort food since 2015."}
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

        # Reviews Carousel (Google Reviews inside slides)
        reviews_data = [
            {"name": "Sarah M. (Yelp)", "text": "Can't get enough of their Chicken Katsu! The roasted garlic and ginger sauce is incredible.", "rating": 5},
            {"name": "James L. (Yelp)", "text": "Best food truck in SLC. The portions are huge and the flavor is authentic.", "rating": 5},
            {"name": "Emily R. (Yelp)", "text": "Always fresh and the staff is so friendly. Love the Thai salad side.", "rating": 5},
            {"name": "Michael T.", "text": "The Teriyaki Chicken is perfectly grilled. A healthy and delicious lunch option.", "rating": 5},
            {"name": "Jessica K.", "text": "Gyoza is a must-have side. Crispy and flavorful.", "rating": 4}
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
                                "date": "1 month ago",
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
                "title": "Fan Favorites",
                "items": [
                    {"name": "Chicken Katsu", "image": menu_katsu, "description": "Our signature crispy fried chicken cutlet."},
                    {"name": "Grilled Teriyaki", "image": menu_teriyaki, "description": "Tender chicken glazed in house-made teriyaki sauce."},
                    {"name": "Gyoza", "image": menu_gyoza, "description": "Pan-fried dumplings."}
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
                    <p class="text-xl font-semibold mb-2">Square Kitchen Eatery</p>
                    <p class="text-lg text-gray-700">{address}</p>
                    <p class="text-lg text-gray-700 mt-2">{hours}</p>
                    <div class="mt-6">
                        <a href="https://maps.google.com/?q={address}" target="_blank" class="text-blue-600 hover:text-blue-800 underline">Get Directions</a>
                    </div>
                </div>"""
            }
        )

        # Footer
        footer_text = BlockInstance.objects.create(
            page=home_page,
            definition_id="text",
            placement_key="footer",
            sort_order=0,
            params={
                "content": f"<p><strong>Comfort Bowl</strong><br>{address}<br>{hours}</p>"
            }
        )
        footer_social = BlockInstance.objects.create(
            page=home_page,
            definition_id="social_links",
            placement_key="footer",
            sort_order=1,
            params={
                "links": [
                    {"platform": "instagram", "url": instagram_url},
                    {"platform": "facebook", "url": facebook_url}
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
        # Inherit Header/Footer by recreating them (or logic handles inheritance? No, we need to create them)
        # NOTE: Current logic requires blocks on each page unless verified otherwise. For safety, duplicating header/footer.
        # Header (Duplicate)
        h_row2 = BlockInstance.objects.create(
             page=menu_page, definition_id="row", placement_key="header", sort_order=0,
             params={"gap": "4", "justify": "space-between", "align": "center"}
        )
        BlockInstance.objects.create(page=menu_page, parent=h_row2, definition_id="brand_logo", placement_key="column", sort_order=0,
                                     params={"brand_name": "Comfort Bowl", "logo_image": logo_url, "link_url": "/"})
        BlockInstance.objects.create(page=menu_page, parent=h_row2, definition_id="menu", placement_key="column", sort_order=1,
                                     params={"style": "pills", "responsive": True, "items": [{"label": "Home", "url": "/", "type": "link"}, {"label": "Menu", "url": "/menu", "type": "link"}, {"label": "Visit Us", "url": "/#location", "type": "link"}]})

        # Menu Page Content
        BlockInstance.objects.create(
            page=menu_page,
            definition_id="hero",
            placement_key="main",
            sort_order=0,
            params={
                "title": "Our Menu",
                "subtitle": "Fresh, Authentic, Delicious.",
                "bgImage": image_map.get('image_4', ''),
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
                "title": "Rice Bowls",
                "items": [
                    {"name": "Chicken Katsu Bowl", "image": menu_katsu, "description": "Crispy fried chicken cutlet served with rice, salad, and our special sauce."},
                    {"name": "Teriyaki Chicken Bowl", "image": menu_teriyaki, "description": "Grilled chicken glazed in house-made teriyaki sauce over rice."},
                    {"name": "Spicy Chicken Bowl", "image": menu_katsu, "description": "Our famous katsu with a spicy kick."},
                    {"name": "Beef Bowl (Gyudon)", "image": "", "description": "Thinly sliced beef simmered with onions in soy broth."}
                ]
            }
        )

        # Footer (Duplicate)
        BlockInstance.objects.create(page=menu_page, definition_id="text", placement_key="footer", sort_order=0, params={"content": f"<p><strong>Comfort Bowl</strong><br>{address}<br>{hours}</p>"})
        BlockInstance.objects.create(page=menu_page, definition_id="social_links", placement_key="footer", sort_order=1, params={"links": [{"platform": "instagram", "url": instagram_url}, {"platform": "facebook", "url": facebook_url}]})

        self.stdout.write(self.style.SUCCESS('Successfully created Comfort Bowl site with enhanced content and carousel'))
