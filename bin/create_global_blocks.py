import os
import django
import sys

sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website, BlockDefinition, BlockInstance

def create_global_blocks(slug):
    try:
        website = Website.objects.get(slug=slug)
        print(f"Adding global blocks to: {website.name}")
        
        # Clear existing global blocks to avoid duplicates if re-run
        BlockInstance.objects.filter(website=website, page=None).delete()
        
        # --- HEADER ---
        # 1. Brand Logo
        try:
            brand_def = BlockDefinition.objects.get(id='brand_logo')
            BlockInstance.objects.create(
                website=website,
                definition=brand_def,
                placement_key='header',
                sort_order=0,
                params={
                    'brand_name': "Cairn's Counseling Center",
                    'logo_image': '/cairn-icon.png',
                    'tagline': "Healing • Transformation • Growth",
                    'link_url': '/'
                }
            )
            print("Added Brand Logo")
        except BlockDefinition.DoesNotExist:
            print("brand_logo definition not found")

        # 2. Menu
        try:
            menu_def = BlockDefinition.objects.get(id='menu')
            BlockInstance.objects.create(
                website=website,
                definition=menu_def,
                placement_key='header',
                sort_order=1,
                params={
                    'items': [
                        {'label': 'Counseling', 'url': '/counseling/', 'type': 'page'},
                         # Add more if needed, currently only Counseling is in config
                    ],
                    'style': 'pills',
                    'responsive': True,
                    'hamburgerDirection': 'dropdown'
                }
            )
            print("Added Menu")
        except BlockDefinition.DoesNotExist:
            print("menu definition not found")

        # --- FOOTER ---
        # Footer container with 3 columns (Location 1, Location 2, Copyright/Info)
        
        # Using a Row block for layout
        try:
            row_def = BlockDefinition.objects.get(id='row')
            col_def = BlockDefinition.objects.get(id='column')
            text_def = BlockDefinition.objects.get(id='text')
            
            # Row
            footer_row = BlockInstance.objects.create(
                website=website,
                definition=row_def,
                placement_key='footer',
                sort_order=0,
                params={'gap': '8', 'justify': 'center', 'css_classes': 'py-8 text-slate-600 text-sm'}
            )
            
            # Col 1: Provo Office
            col1 = BlockInstance.objects.create(
                website=website,
                definition=col_def,
                parent=footer_row,
                placement_key='column',
                sort_order=0,
                params={'width': 'auto'}
            )
            BlockInstance.objects.create(
                website=website,
                definition=text_def,
                parent=col1,
                placement_key='blocks',
                sort_order=0,
                params={'content': '<strong>Provo Office</strong><br>180 N. University Ave., Suite 270<br>Provo, UT 84601'}
            )
            
            # Col 2: Lehi Office
            col2 = BlockInstance.objects.create(
                website=website,
                definition=col_def,
                parent=footer_row,
                placement_key='column',
                sort_order=1,
                params={'width': 'auto'}
            )
            BlockInstance.objects.create(
                website=website,
                definition=text_def,
                parent=col2,
                placement_key='blocks',
                sort_order=0,
                params={'content': '<strong>Lehi Office</strong><br>3450 N. Triumph Blvd., Suite 102<br>Lehi, UT 84043'}
            )
            
            # Col 3: Copyright / Phone
            col3 = BlockInstance.objects.create(
                website=website,
                definition=col_def,
                parent=footer_row,
                placement_key='column',
                sort_order=2,
                params={'width': 'auto'}
            )
            BlockInstance.objects.create(
                website=website,
                definition=text_def,
                parent=col3,
                placement_key='blocks',
                sort_order=0,
                params={'content': '<strong>Contact</strong><br>+1234567890<br>© 2024 Cairn\'s Counseling Center'}
            )
            
            print("Added Footer Blocks")
            
        except BlockDefinition.DoesNotExist as e:
            print(f"Block definition missing: {e}")

    except Website.DoesNotExist:
        print(f"Website '{slug}' not found.")

if __name__ == "__main__":
    create_global_blocks('cairnscounselingcenterv2')
