
from django.core.management.base import BaseCommand
from django.conf import settings
from hugo.models import Website, Page, BlockInstance
from pathlib import Path
import shutil
import os
import json

class Command(BaseCommand):
    help = 'Generate Hugo site files (Restored Logic + Media Fix)'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Website slug')

    def handle(self, *args, **options):
        slug = options['slug']
        try:
            website = Website.objects.get(slug=slug)
        except Website.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Website '{slug}' not found."))
            return

        self.stdout.write(f"Generating site for: {website.name} ({website.slug})")

        # Define Output paths
        output_dir = Path(settings.BASE_DIR) / 'hugo_output' / website.slug
        content_dir = output_dir / 'content'
        static_dir = output_dir / 'static'
        
        # Clean
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        content_dir.mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate Site Config (hugo.toml)
        self.generate_config(output_dir, website)

        # 2. Generate Layouts (Templates)
        self.generate_layouts(output_dir)
        self.generate_fixed_templates(output_dir) # Overwrite with fixed ones if needed

        # 3. Generate Pages (Using ORIGINAL views.py logic)
        self.generate_pages_original(website, content_dir)
        
        # 4. Copy Media (The Fix)
        self.copy_media(website, static_dir)
        
        self.stdout.write(self.style.SUCCESS(f"Site generated in {output_dir}"))

    def generate_config(self, output_dir, website):
        # Basic config generation
        with open(output_dir / 'hugo.toml', 'w') as f:
            f.write(f"""
baseURL = 'https://{website.slug}.monu.dev'
languageCode = 'en-us'
title = '{website.name}'
theme = []

[params]
    description = '{getattr(website, "description", "")}'
    
[mediaTypes]
[mediaTypes."text/css"]
    suffixes = ["css"]
            """)

    def generate_layouts(self, output_dir):
        # Basic layout generation
        layouts = output_dir / 'layouts'
        defaults = layouts / '_default'
        partials = layouts / 'partials'
        blocks = partials / 'blocks'
        
        for d in [layouts, defaults, partials, blocks]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Baseof
        with open(defaults / 'baseof.html', 'w') as f:
            f.write("""<!DOCTYPE html>
<html lang="{{ .Site.LanguageCode }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ .Title }} | {{ .Site.Title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/css/custom.css">
</head>
<body class="bg-slate-50 text-slate-800 font-sans min-h-screen flex flex-col">
    {{ block "main" . }}{{ end }}
</body>
</html>""")
        
        # Single/List
        single = """{{ define "main" }}
<div class="flex flex-col min-h-screen">
    <header class="w-full border-b bg-white border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        {{ range .Params.header_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
        </div>
    </header>
    <main class="flex-1 w-full">
        {{ range .Params.main_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </main>
    <footer class="w-full mt-auto border-t bg-gray-900 border-gray-800 text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {{ range .Params.footer_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
        </div>
    </footer>
</div>
{{ end }}"""
        with open(defaults / 'single.html', 'w') as f: f.write(single)
        with open(defaults / 'list.html', 'w') as f: f.write(single)
        
        # Render Block Partial
        with open(blocks / 'render-block.html', 'w') as f:
             f.write("""{{ if .type }}
    {{ $partialPath := printf "blocks/%s.html" .type }}
    {{ if templates.Exists (printf "partials/%s" $partialPath) }}
        {{ partial $partialPath . }}
    {{ else }}
        <div class="p-4 border border-red-200 bg-red-50 text-red-700 rounded my-4">
            <strong>Missing Block Template:</strong> {{ .type }}
        </div>
    {{ end }}
{{ end }}""")

    def generate_fixed_templates(self, output_dir):
        # Includes the fixed menu and features templates
        blocks = output_dir / 'layouts' / 'partials' / 'blocks'
        
        fixed_features = """
<div class="py-16 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-6xl mx-auto flex flex-wrap justify-center gap-8">
        {{ range .features }}
        <div class="w-full md:w-1/3 lg:w-1/4 text-center p-6 rounded-lg hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 bg-white border border-slate-100">
            {{ if .icon }}
            <div class="w-16 h-16 mx-auto mb-4 bg-red-100 text-red-600 rounded-full flex items-center justify-center shadow-sm">
                 {{ if eq .icon "truck" }}<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0"></path></svg>
                 {{ else if eq .icon "leaf" }}<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                 {{ else }}<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path></svg>
                 {{ end }}
            </div>
            {{ end }}
            <h4 class="text-xl font-bold mb-3 text-slate-800">{{ .title }}</h4>
            <p class="text-slate-600 leading-relaxed">{{ .description }}</p>
        </div>
        {{ end }}
    </div>
</div>"""

        fixed_menu = """
<div class="py-12 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-10" style="color: var(--color-text, #1f2937);">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {{ range .items }}
        <div class="group bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 border border-slate-100 flex flex-col h-full">
            {{ if .image }}
            <div class="relative h-48 overflow-hidden bg-gray-100">
                <img src="{{ .image }}?v=2" alt="{{ .name }}" 
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                     onerror="this.onerror=null;this.parentElement.style.display='none';"/>
            </div>
            {{ end }}
            <div class="p-5 flex-1 flex flex-col">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="text-lg font-bold text-slate-900 leading-tight">{{ .name }}</h4>
                </div>
                {{ if .description }}
                <p class="text-sm text-slate-500 leading-snug flex-1">{{ .description }}</p>
                {{ end }}
                <div class="mt-4 pt-4 border-t border-slate-50 flex items-center justify-between text-xs font-medium text-slate-400 uppercase tracking-wider">
                     <span>Menu Item</span>
                     <span class="text-red-600">Order Now</span>
                </div>
            </div>
        </div>
        {{ end }}
    </div>
</div>"""
        with open(blocks / 'features_grid.html', 'w') as f: f.write(fixed_features)
        with open(blocks / 'menu_grid.html', 'w') as f: f.write(fixed_menu)
        
        # Write generic fallback for others if they don't exist
        for name in ['hero', 'text', 'gallery', 'stats', 'embed', 'cta_hero', 'social_links', 'faq', 'google_reviews', 'flip_cards', 'process_steps']:
             if not (blocks / f'{name}.html').exists():
                 with open(blocks / f'{name}.html', 'w') as f: f.write(f'<div class="{name}">{{{{ . | jsonify }}}}</div>')


    def generate_pages_original(self, website, content_dir):
        import json
        for page in website.pages.all():
            page_data = self._build_page_dict(page)
            
            # Serialize to JSON (valid YAML) wrapped in ---
            # This is the safest way to handle complex nested content without syntax errors
            frontmatter = json.dumps(page_data, indent=2)
            content = f"---\n{frontmatter}\n---\n"
            
            if page.slug == '/' or page.slug == '':
                path = content_dir / '_index.md'
            else:
                 path = content_dir / page.slug.strip('/') / 'index.md'
                 path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f: f.write(content)

    def _build_page_dict(self, page):
        # Build dictionary structure for the page
        data = {
            'title': page.title,
            # 'params': {} # Flattened now
        }
        
        if page.description:
            data['description'] = page.description
            
        is_homepage = (page.slug == '/' or page.slug == '')
        if is_homepage:
            data['type'] = page.layout
        else:
            data['layout'] = page.layout
            
        # Helper to recursively build block list
        def build_blocks(blocks_list):
            out_blocks = []
            
            for block in blocks_list:
                # Handle flex_columns logic
                if block.definition_id == 'flex_columns':
                    # ... [Same logic as before but building dicts] ...
                    col_widths_str = block.params.get('col_widths', '50.0, 50.0')
                    col_widths = [w.strip() for w in col_widths_str.split(',')]
                    
                    fc_children = BlockInstance.objects.filter(parent=block).order_by('sort_order')
                    has_legacy_keys = any(child.placement_key and child.placement_key.startswith('col_') for child in fc_children)
                    
                    row_block = {
                        'type': 'row',
                        'flex_mode': True,
                        'gap': "2",
                        'blocks': [] # Will hold columns or content
                    }
                    if block.params.get('css_classes'):
                        row_block['css_classes'] = block.params['css_classes']
                        
                    if not has_legacy_keys and fc_children.exists():
                        # New format: children directly in row
                        row_block['blocks'] = build_blocks(fc_children)
                    else:
                        # Legacy format: wrap in columns
                        children_by_col = {}
                        for child in fc_children:
                            col_key = child.placement_key or 'col_0'
                            if col_key not in children_by_col: children_by_col[col_key] = []
                            children_by_col[col_key].append(child)
                            
                        for col_index, width in enumerate(col_widths):
                            col_key = f'col_{col_index}'
                            col_children = children_by_col.get(col_key, [])
                            
                            col_block = {
                                'type': 'column',
                                'width_percent': width,
                                'blocks': []
                            }
                            if col_children:
                                col_block['blocks'] = build_blocks(col_children)
                            
                            row_block['blocks'].append(col_block)
                            
                    out_blocks.append(row_block)
                    continue

                # Standard Block
                block_data = block.params.copy() if block.params else {}
                block_data['type'] = block.definition.id
                
                # Recurse children
                children = BlockInstance.objects.filter(parent=block).order_by('sort_order')
                if children.exists():
                    block_data['blocks'] = build_blocks(children)
                    
                out_blocks.append(block_data)
                
            return out_blocks

        # Build Zones
        header = page.main_blocks.filter(placement_key='header').order_by('sort_order')
        main = page.main_blocks.filter(placement_key='main').order_by('sort_order')
        footer = page.main_blocks.filter(placement_key='footer').order_by('sort_order')
        
        # Flatten params to root level to ensure .Params.main_blocks works
        if header.exists(): data['header_blocks'] = build_blocks(header)
        if main.exists(): data['main_blocks'] = build_blocks(main)
        if footer.exists(): data['footer_blocks'] = build_blocks(footer)
        
        return data
        
    def copy_media(self, website, static_dir):
        media_root = Path(settings.MEDIA_ROOT)
        static_media = static_dir / 'media'
        static_media.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for uf in website.files.all():
             src = media_root / uf.file_path
             if src.exists():
                 # Destination: static/media/uploads/filename.ext
                 dst = static_media / uf.file_path
                 dst.parent.mkdir(parents=True, exist_ok=True)
                 shutil.copy2(src, dst)
                 count += 1
        self.stdout.write(f"Copied {count} media files.")
