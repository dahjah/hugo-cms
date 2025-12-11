import json
import os
from django.core.management.base import BaseCommand
from hugo.models import SiteTemplate
from hugo.scrapers.yelp import YelpScraper
from hugo.scrapers.instagram import InstagramScraper
from hugo.scrapers.ftl import FoodTruckLeagueScraper as FTLScraper
from hugo.scrapers.base import BusinessProfile
from hugo.utils.image_colors import extract_colors_from_url
from hugo.llm.content_gen import generate_site_copy

class Command(BaseCommand):
    help = 'Orchestrate Strippin Dippin Chicken site generation via Food Truck V2 template'

    def handle(self, *args, **options):
        # 1. Inputs
        yelp_url = "https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan"
        insta_url = "https://www.instagram.com/strippindippinchicken/"
        ftl_url = "https://foodtruckleague.com/Utah/trucks/677ec632f7fd49c21152b236"
        
        profile_path = "strippin_profile.json"
        
        # 2. Scrape or Load Profile
        if os.path.exists(profile_path):
            self.stdout.write(f"Loading profile from {profile_path}...")
            with open(profile_path, 'r') as f:
                data = json.load(f)
                # Reconstruct generic objects? Or just use dict.
                # Simplest is to keep it as dict for analysis, OR reconstruct.
                # Let's try to reconstruct basic fields.
                profile = BusinessProfile(**{k: v for k, v in data.items() if k in BusinessProfile.__annotations__})
                # Re-assign complex lists manually if needed, or trust kwargs
                profile.reviews = data.get('reviews', [])
                profile.menu_items = data.get('menu_items', [])
                profile.stats = data.get('stats', {})
                profile.colors = data.get('colors', {})
        else:
            self.stdout.write("Scraping fresh data...")
            profile = BusinessProfile(name="Strippin Dippin Chicken")
            
            # Yelp
            try:
                self.stdout.write("Running Yelp Scraper...")
                y_profile = YelpScraper.scrape_url(yelp_url)
                profile.merge(y_profile)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Yelp Error: {e}"))

            # Instagram
            try:
                self.stdout.write("Running Instagram Scraper...")
                i_profile = InstagramScraper.scrape_url(insta_url)
                profile.merge(i_profile)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Instagram Error: {e}"))
                
            # FTL
            try:
                self.stdout.write("Running FTL Scraper...")
                f_profile = FTLScraper.scrape_url(ftl_url)
                profile.merge(f_profile)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"FTL Error: {e}"))
                
            # Colors
            if profile.logo_url:
                self.stdout.write(f"Generating Colors from {profile.logo_url}...")
                palette, css = extract_colors_from_url(profile.logo_url)
                if palette:
                    profile.colors = palette
                    profile.colors_css = css
            
            # Save to Disk
            with open(profile_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f"Profile saved to {profile_path}"))

        # 3. Load Template
        try:
            template = SiteTemplate.objects.get(slug='food-truck-v2')
            self.stdout.write(f"Loaded Template: {template.name}")
        except SiteTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR("Template 'food-truck-v2' not found!"))
            return

        # 4. Gap Analysis
        self.stdout.write("\n--- GAP ANALYSIS ---")
        
        missing_data = []
        recommendations = []
        
        # Check Core Data
        # Sanitize Logo: Instagram URLs are ephemeral and break.
        # But User provided a specific valid link we need to download.
        # We'll override it here so the downloader sees it.
        profile.logo_url = "https://scontent-den2-1.cdninstagram.com/v/t51.2885-19/132955810_824625285053035_230977350139597472_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-den2-1.cdninstagram.com&_nc_cat=107&_nc_oc=Q6cZ2QEl7mfUjLt5UAWA4TYcMB0THd9f61hUdYIypkcGD3TOSQ4-OJHumabugCDZwg4CnxM&_nc_ohc=GwdXFAA7lVUQ7kNvwEmy8mD&_nc_gid=W-Xn5wbVUCq5Es1GDlPLpA&edm=AEYEu-QBAAAA&ccb=7-5&oh=00_AfnK7d0FB1RdBMhGpi4d4tqCc8O3MRHzTt9tLb9jpCKkMg&oe=693FE36F&_nc_sid=ead929"

        if not profile.description: missing_data.append("Business Description")
        if not profile.tagline: missing_data.append("Tagline")
        if not profile.hours: missing_data.append("Opening Hours")
        if not profile.email: missing_data.append("Email Address")
        if not profile.phone: missing_data.append("Phone Number")
        
        # Check Template Block Requirements
        template_pages = template.pages_json.get('pages', [])
        # Also check global blocks
        template_blocks = []
        
        def collect_block_types(blocks):
            for b in blocks:
                # 'type' is used in the JSON (maps to definition_id)
                b_id = b.get('type') or b.get('id')
                if b_id:
                    template_blocks.append(b_id)
                # Recursively check children
                if b.get('children'):
                    collect_block_types(b['children'])

        for page in template_pages:
            collect_block_types(page.get('blocks', []))
        
        # Also globals
        collect_block_types(template.pages_json.get('global_blocks', []))

        # Flatten for easy checking
        unique_blocks = set(template_blocks)
        
        if 'features_grid' in unique_blocks:
            # We don't have structured 'features' in profile (LLM job)
            missing_data.append("Structured Features (LLM needed)")
            
        if 'stats_counter' in unique_blocks:
            if not profile.stats: 
                missing_data.append("Statistics (Followers/Reviews)")
            elif len(profile.stats) < 3:
                # Add review count if available to mapping, handled in generation
                pass
                
        if 'menu_grid' in unique_blocks:
            if not profile.menu_items and not profile.gallery_images:
                missing_data.append("Menu Items OR Gallery Images for Menu")
            if not profile.menu_items:
                recommendations.append("Menu items are missing. Will attempt to synthesize from reviews.")

        if 'google_reviews' in unique_blocks: 
            if not profile.reviews:
                missing_data.append("Customer Reviews")
            else:
                self.stdout.write(f"✓ Have {len(profile.reviews)} reviews.")

        # Report Missing
        if missing_data:
            self.stdout.write(self.style.WARNING("Missing Data Points:"))
            for m in missing_data:
                self.stdout.write(f" - {m}")
        else:
            self.stdout.write(self.style.SUCCESS("✓ All core data points populated!"))
            
        # Report Recommendations
        if recommendations:
            self.stdout.write(self.style.NOTICE("Recommendations:"))
            for r in recommendations:
                self.stdout.write(f" . {r}")

        # 5. Synthesize Content
        self.stdout.write("Synthesizing missing content via LLM...")
        requirements = ["features_grid", "hero_headline", "hero_subheadline", "about_content", "catering_faq"]
        
        # If no menu items, ask LLM to synthesize them
        if not profile.menu_items:
            requirements.append("menu_items")
            
        synthesized_content = generate_site_copy(profile, requirements=requirements)

        # 6. Populate State
        filled_state = {
            "website_name": profile.name, 
            "custom_css": profile.colors_css or template.base_css,
            "pages": [],
            "global_blocks": []
        }
        
        def fill_blocks(blocks):
            filled = []
            for t_block in blocks:
                new_block = t_block.copy()
                b_id = new_block.get('type') # Start using type
                params = new_block.get('params', {}).copy()
                
                # --- FILLING LOGIC ---
                if b_id == 'hero':
                    params['title'] = synthesized_content.get('hero_headline') or profile.tagline or profile.name
                    params['subtitle'] = synthesized_content.get('hero_subheadline') or (profile.description or "")[:150] + "..."
                    params['bgImage'] = profile.hero_image_url or params.get('bgImage', '')
                    if not params.get('cta_text'): params['cta_text'] = "View Menu"
                
                elif b_id == 'features_grid':
                    if 'features_grid' in synthesized_content:
                        f_items = []
                        for f in synthesized_content['features_grid']:
                            f_items.append({
                                'title': f['title'],
                                'description': f['description'],
                                'icon': 'star'
                            })
                        params['items'] = f_items

                elif b_id == 'brand_logo':
                    params['brand_name'] = profile.name
                    params['logo_image'] = profile.logo_url
                    
                elif b_id == 'social_links':
                    links = []
                    if yelp_url: links.append({'platform': 'yelp', 'url': yelp_url})
                    if insta_url: links.append({'platform': 'instagram', 'url': insta_url})
                    if ftl_url: links.append({'platform': 'website', 'url': ftl_url})
                    params['links'] = links
                    
                elif b_id == 'stats_counter':
                    s_list = []
                    for k, v in profile.stats.items():
                        s_list.append({'value': str(v), 'label': k.capitalize(), 'suffix': ''})
                    if profile.stats.get('review_count') and 'reviews' not in profile.stats:
                         s_list.append({'value': str(profile.stats.get('review_count')), 'label': 'Reviews', 'suffix': '+'})
                    params['stats'] = s_list # Corrected key to match template

                elif b_id == 'google_reviews':
                    r_list = []
                    for r in profile.reviews[:6]: 
                         if isinstance(r, dict):
                            r_list.append({
                                'name': r.get('author'), 'rating': r.get('rating'), 'text': r.get('text'), 
                                'image': r.get('author_image', '')
                            })
                         else:
                            r_list.append({
                                'name': r.author, 'rating': r.rating, 'text': r.text,
                                'image': r.author_image
                            })
                    params['reviews'] = r_list
                    
                elif b_id == 'menu_grid':
                    m_list = []
                    # 1. Prefer Real Menu Items (Scraped)
                    if profile.menu_items:
                        for item in profile.menu_items[:12]: # Show up to 12 items
                             if isinstance(item, dict):
                                 m_list.append({
                                     'name': item.get('name'), 
                                     'image': item.get('image_url') or '',
                                     'description': f"{item.get('description', '')} ({item.get('price', '')})".strip()
                                 })
                             else:
                                 m_list.append({
                                     'name': item.name, 
                                     'image': item.image_url,
                                     'description': f"{item.description} ({item.price})".strip()
                                 })
                    
                    # 2. Use Synthesized Menu Items (LLM)
                    elif 'menu_items' in synthesized_content:
                        for item in synthesized_content['menu_items']:
                             m_list.append({
                                 'name': item.get('name', 'Delicious Item'),
                                 'image': '', # No image for synthesized items
                                 'description': f"{item.get('description', '')} ({item.get('price', '')})".strip()
                             })

                    # 3. Fallback to Gallery Images if no menu items
                    elif profile.gallery_images:
                        for img in profile.gallery_images[:8]:
                             m_list.append({'name': '', 'image': img, 'description': ''})
                    
                    params['items'] = m_list
                
                elif b_id == 'carousel':
                    # Populate carousel with gallery images
                    if profile.gallery_images:
                        carousel_items = []
                        # Use top 5 images
                        for img in profile.gallery_images[:5]:
                            carousel_items.append({
                                'type': 'image',
                                'params': {'src': img, 'alt': 'Gallery Image'}
                            })
                        # Carousels store items in children
                        new_block['children'] = carousel_items
                
                elif b_id == 'text':
                    # Heuristic: Find specific text blocks by context?
                    # About content usually follows a 'flex_columns' or is in 'about' section.
                    # For now, if we have about_content and the block is in a section with style 'light' or id 'about'
                    # But verifying 'id' of parent section is hard here as we are recursing.
                    # However, we can use placement_key or just fill first massive Markdown block?
                    
                    # Better approach: check content. But content is empty.
                    pass 
                
                elif b_id == 'markdown':
                     if synthesized_content.get('about_content'):
                         # Very crude heuristic: fill any empty markdown block with about content?
                         # Or better, let's target the 'About' section specifically in the page loop if possible.
                         # Instead, let's just fill it if params['content'] is empty.
                         if not params.get('content'):
                             params['content'] = synthesized_content['about_content']

                elif b_id == 'accordion':
                     if synthesized_content.get('catering_faq'):
                         a_items = []
                         for faq in synthesized_content['catering_faq']:
                             a_items.append({'title': faq['question'], 'content': faq['answer']})
                         params['items'] = a_items

                # Recurse
                if new_block.get('children'):
                    new_block['children'] = fill_blocks(new_block['children'])
                
                new_block['params'] = params
                filled.append(new_block)
            return filled

        for t_page in template_pages:
            filled_page = t_page.copy()
            filled_page['blocks'] = fill_blocks(t_page.get('blocks', []))
            filled_state['pages'].append(filled_page)
            
        filled_state['global_blocks'] = fill_blocks(template.pages_json.get('global_blocks', []))
            
        # Save State
        state_path = "strippin_site_state.json"
        with open(state_path, 'w') as f:
            json.dump(filled_state, f, indent=2)
            
        self.stdout.write(self.style.SUCCESS(f"\nFinal Site State saved to {state_path}"))
        
        # 7. Create Site in DB (Ingestion)
        self.stdout.write("\n--- INGESTING SITE TO DB ---")
        from hugo.models import Website, Page, BlockInstance, BlockDefinition
        from django.db import transaction

        with transaction.atomic():
            # Create Website
            site_slug = "strippin-v2"
            Website.objects.filter(slug=site_slug).delete() # Cleanup previous runs
            
            website = Website.objects.create(
                name="Strippin Dippin Chicken V2",
                slug=site_slug,
                custom_css=filled_state.get('custom_css', '')
            )
            self.stdout.write(f"Created Website: {website.name} ({website.id})")
            
            # --- ASSET DOWNLOADING ---
            import requests
            import mimetypes
            from django.conf import settings
            from hugo.models import UploadedFile
            from pathlib import Path
            import uuid
            
            def download_and_cache(url, website):
                if not url or not url.startswith('http'): 
                    return url
                    
                try:
                    # Deduplicate based on URL or just always download? 
                    # For now simplicity: always download new file
                    resp = requests.get(url, stream=True, timeout=10)
                    if resp.status_code == 200:
                        content_type = resp.headers.get('content-type')
                        ext = mimetypes.guess_extension(content_type) or ".jpg"
                        filename = f"{uuid.uuid4()}{ext}"
                        
                        rel_path = f"uploads/{filename}"
                        full_path = Path(settings.MEDIA_ROOT) / "uploads" / filename
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(full_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                                
                        # Create Record safely
                        file_size = full_path.stat().st_size
                        
                        try:
                            with transaction.atomic():
                                UploadedFile.objects.create(
                                    website=website,
                                    filename=filename,
                                    file_path=rel_path,
                                    file_url=f"/media/{rel_path}",
                                    file_size=file_size,
                                    content_type=content_type or 'application/octet-stream'
                                )
                            self.stdout.write(f"   v Downloaded {filename} from {url[:30]}...")
                            return f"/media/{rel_path}"
                        except Exception as e:
                             self.stdout.write(self.style.ERROR(f"Failed to save UploadedFile record: {e}"))
                             # If DB fails, fallback to external URL or just break?
                             # Return URL so site functions but without local asset ref if DB fails
                             return url
                             
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to download {url}: {e}"))
                return url

            def recursive_asset_download(blocks, website):
                for block in blocks:
                    params = block.get('params', {})
                    # 1. Direct fields
                    for key in ['bgImage', 'logo_image', 'image', 'src']:
                        if params.get(key):
                            params[key] = download_and_cache(params[key], website)
                    
                    # 2. Lists (items, reviews)
                    if params.get('items'):
                        for item in params['items']:
                            if item.get('image'):
                                item['image'] = download_and_cache(item['image'], website)
                            if item.get('src'):
                                item['src'] = download_and_cache(item['src'], website)
                                
                    if params.get('reviews'):
                         for r in params['reviews']:
                             if r.get('image'):
                                 r['image'] = download_and_cache(r['image'], website)
                                 
                    if block.get('children'):
                        recursive_asset_download(block['children'], website)

            self.stdout.write(" - Downloading Assets...")
            # Update State in place
            result_pages = filled_state.get('pages', [])
            for p in result_pages:
                 recursive_asset_download(p.get('blocks', []), website)
            
            result_globals = filled_state.get('global_blocks', [])
            recursive_asset_download(result_globals, website)
            
            # --- END ASSET DOWNLOADING ---

            def ingest_blocks(blocks_data, website, page=None, parent=None):
                for i, b_data in enumerate(blocks_data):
                    b_type = b_data.get('type')
                    if not b_type: continue
                    
                    try:
                        definition = BlockDefinition.objects.get(id=b_type)
                    except BlockDefinition.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Block Definition '{b_type}' not found. Skipping."))
                        continue
                        
                    instance = BlockInstance.objects.create(
                        website=website,
                        definition=definition,
                        page=page,
                        parent=parent,
                        placement_key=b_data.get('placement_key', 'main'),
                        sort_order=i,
                        params=b_data.get('params', {})
                    )
                    
                    if b_data.get('children'):
                        ingest_blocks(b_data['children'], website, page=page, parent=instance)

            # Ingest Pages
            for p_data in filled_state.get('pages', []):
                page = Page.objects.create(
                    website=website,
                    title=p_data.get('title', 'Untitled'),
                    slug=p_data.get('slug', '/'),
                    layout=p_data.get('layout', 'single'),
                    status='published'
                )
                self.stdout.write(f" - Created Page: {page.title}")
                ingest_blocks(p_data.get('blocks', []), website, page=page)
                
            # Ingest Global Blocks
            self.stdout.write(" - Ingesting Global Blocks...")
            ingest_blocks(filled_state.get('global_blocks', []), website, page=None)
            
        self.stdout.write(self.style.SUCCESS(f"Successfully created site '{website.name}' with {website.pages.count()} pages."))
