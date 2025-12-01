from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
import uuid 
from .models import Page, BlockDefinition, BlockInstance, LayoutTemplate, Website
from .serializers import (
    PageListSerializer, 
    PageDetailSerializer, 
    BlockDefinitionSerializer, 
    BlockInstanceSerializer,
    BlockInstanceSerializer,
    SiteConfigSerializer,
    WebsiteSerializer
)
from .importer import import_hugo_theme_structure

def editor_view(request):
    """Serves the Vue.js frontend application."""
    return render(request, 'hugo/index.html')
class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    
    def perform_create(self, serializer):
        # Save the new website
        website = serializer.save()
        
        # Automatically create a Home page for the new website
        Page.objects.create(
            website=website,
            title='Home',
            slug='/',
            layout='single',
            status='draft'
        )

class CmsInitViewSet(viewsets.ViewSet):
    
    def list(self, request):
        definitions = BlockDefinition.objects.all()
        layouts = LayoutTemplate.objects.all()
        websites = Website.objects.all()
        
        # Determine current website
        website_id = request.query_params.get('website_id')
        if website_id:
            current_website = Website.objects.filter(id=website_id).first()
        else:
            current_website = websites.first()
            
        if not current_website:
            # Should not happen if migration ran, but handle gracefully
            current_website = Website.objects.create(name="Default Site", slug="default")
            websites = Website.objects.all()

        # Global blocks are defined by having parent=null, page=null AND website=current_website
        header_blocks = BlockInstance.objects.filter(placement_key='header', page=None, parent=None, website=current_website).order_by('sort_order')
        footer_blocks = BlockInstance.objects.filter(placement_key='footer', page=None, parent=None, website=current_website).order_by('sort_order')
        
        data = {
            'definitions': definitions,
            'layouts': layouts,
            'header': header_blocks,
            'footer': footer_blocks,
            'websites': websites,
            'current_website': current_website
        }
        serializer = SiteConfigSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def save_globals(self, request):
        """Saves header and footer blocks using the new relational structure."""
        
        # Helper to collect all UUIDs for deletion check
        incoming_ids = []
        def collect_ids(blocks):
            for block in blocks:
                incoming_ids.append(block['id'])
                if block.get('children'):
                    # The Vue frontend sends an array of column objects, each having a 'blocks' array
                    for col in block['children']:
                        if col.get('blocks'):
                            collect_ids(col['blocks'])
        
        collect_ids(request.data.get('header', []))
        collect_ids(request.data.get('footer', []))
        
        try:
            with transaction.atomic():
                # Delete old global blocks not present in the new payload for this website
                website_id = request.data.get('website_id')
                if not website_id:
                     return Response({'error': 'website_id is required'}, status=status.HTTP_400_BAD_REQUEST)
                
                website = Website.objects.get(id=website_id)

                BlockInstance.objects.filter(page=None, parent=None, website=website).exclude(id__in=incoming_ids).delete()
                
                # Save new/updated blocks recursively
                self._save_blocks_recursive(request.data.get('header', []), placement_key='header', page=None, website=website)
                self._save_blocks_recursive(request.data.get('footer', []), placement_key='footer', page=None, website=website)

            return Response({'status': 'saved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _save_blocks_recursive(self, blocks_data, placement_key, page, parent=None, website=None):
        """Helper to save a list of blocks and their children."""
        for index, block_data in enumerate(blocks_data):
            # Ensure ID exists for update_or_create; generate new if necessary
            block_id = block_data.get('id') or uuid.uuid4()
            
            block_instance, _ = BlockInstance.objects.update_or_create(
                id=block_id,
                defaults={
                    'definition_id': block_data['type'],
                    'page': page,
                    'parent': parent,
                    'website': website,
                    'placement_key': placement_key,
                    'sort_order': index,
                    'params': block_data.get('params', {})
                }
            )
            
            # --- Handle Children (Nesting) ---
            if block_data.get('children'):
                
                # Delete old children of this parent not present in the incoming payload
                incoming_child_ids = []
                for col in block_data['children']:
                     if col.get('blocks'):
                         for child in col['blocks']:
                             if 'id' in child: incoming_child_ids.append(child['id'])
                
                block_instance.children.exclude(id__in=incoming_child_ids).delete()

                for col_index, col_data in enumerate(block_data['children']):
                    # This handles the column structure sent by the Vue frontend
                    
                    if col_data.get('blocks'):
                        col_placement_key = f"col_{col_index}"
                        
                        # Recursively save blocks inside the column
                        self._save_blocks_recursive(
                            col_data['blocks'], 
                            placement_key=col_placement_key, 
                            page=None, # Nested blocks do not link to the page directly
                            parent=block_instance, # Link to the 'flex_columns' parent instance
                            website=website
                        )

class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by('-updated_at')
    
    def get_queryset(self):
        queryset = Page.objects.all().order_by('-updated_at')
        website_id = self.request.query_params.get('website_id')
        if website_id:
            queryset = queryset.filter(website_id=website_id)
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PageListSerializer
        return PageDetailSerializer

    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """
        Returns all top-level blocks for this specific page (main, sidebar, etc).
        """
        page = self.get_object()
        # Fetch all top-level blocks for the page, regardless of placement_key
        blocks = BlockInstance.objects.filter(page=page, parent=None).order_by('sort_order')
        serializer = BlockInstanceSerializer(blocks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_content(self, request, pk=None):
        """
        Saves the page metadata and block content using the new relational structure.
        """
        page = self.get_object()
        top_level_blocks_data = request.data.get('blocks', [])
        
        # 1. Collect all UUIDs from the incoming payload (for deletion check)
        all_incoming_ids = []
        def collect_ids(blocks):
            for block in blocks:
                all_incoming_ids.append(block['id'])
                if block.get('children'):
                    # The Vue frontend sends an array of column objects, each having a 'blocks' array
                    for col in block['children']:
                        if col.get('blocks'):
                            collect_ids(col['blocks'])
        collect_ids(top_level_blocks_data)

        try:
            with transaction.atomic():
                # Delete existing blocks belonging to this page that are NOT in the payload
                page.main_blocks.exclude(id__in=all_incoming_ids).delete()
                
                # 2. Group blocks by placement_key (main, sidebar)
                main_blocks = [b for b in top_level_blocks_data if b.get('placement_key') == 'main']
                sidebar_blocks = [b for b in top_level_blocks_data if b.get('placement_key') == 'sidebar']
                
                # 3. Save top-level blocks recursively for each zone
                self._save_blocks_recursive(
                    main_blocks, 
                    placement_key='main', 
                    page=page, 
                    parent=None
                )
                
                self._save_blocks_recursive(
                    sidebar_blocks, 
                    placement_key='sidebar', 
                    page=page, 
                    parent=None
                )
                
                # Update page timestamp to move it to top of list
                page.save()
            
            return Response({'status': 'saved', 'page_id': page.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    def _save_blocks_recursive(self, blocks_data, placement_key, page, parent=None):
        """Helper to save a list of blocks and their children. Same as CmsInitViewSet's helper."""
        for index, block_data in enumerate(blocks_data):
            block_id = block_data.get('id') or uuid.uuid4()
            
            block_instance, _ = BlockInstance.objects.update_or_create(
                id=block_id,
                defaults={
                    'definition_id': block_data['type'],
                    'page': page,
                    'parent': parent,
                    'placement_key': placement_key,
                    'sort_order': index,
                    'params': block_data.get('params', {})
                }
            )
            
            if block_data.get('children'):
                
                incoming_child_ids = []
                for col in block_data['children']:
                     if col.get('blocks'):
                         for child in col['blocks']:
                             if 'id' in child: incoming_child_ids.append(child['id'])
                
                block_instance.children.exclude(id__in=incoming_child_ids).delete()

                for col_index, col_data in enumerate(block_data['children']):
                    if col_data.get('blocks'):
                        col_placement_key = f"col_{col_index}"
                        
                        self._save_blocks_recursive(
                            col_data['blocks'], 
                            placement_key=col_placement_key, 
                            page=None, 
                            parent=block_instance
                        )

    @action(detail=False, methods=['post'])
    def import_theme(self, request):
        """
        Custom endpoint to trigger theme import logic.
        """
        theme_name = request.data.get('theme_name', 'default-mock')
        
        try:
            result = import_hugo_theme_structure(theme_name)
            return Response({'status': 'success', 'message': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def publish(self, request):
        """
        Generate Hugo site files from CMS content and save to filesystem.
        Creates markdown files for pages and hugo.toml for site configuration.
        """
        from pathlib import Path
        from django.conf import settings
        import os
        
        try:
            output_dir = request.data.get('output_dir', None)
            
            # Default Hugo output directory
            if not output_dir:
                website_id = request.data.get('website_id')
                if website_id:
                    website = Website.objects.get(id=website_id)
                    output_dir = os.path.join(settings.BASE_DIR, 'hugo_output', website.slug)
                else:
                    output_dir = os.path.join(settings.BASE_DIR, 'hugo_output', 'default')
            
            output_path = Path(output_dir)
            content_dir = output_path / 'content'
            
            # Create directories
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all pages for this website
            if request.data.get('website_id'):
                pages = Page.objects.filter(website_id=request.data.get('website_id'))
            else:
                pages = Page.objects.all()
            generated_files = []
            
            for page in pages:
                # Generate markdown content for this page
                markdown_content = self._generate_page_markdown(page)
                
                # Determine file path based on slug
                if page.slug == '/' or page.slug == '':
                    file_path = content_dir / '_index.md'
                else:
                    # Remove leading slash and create directory structure
                    slug_path = page.slug.lstrip('/')
                    if '/' in slug_path:
                        # Nested page
                        parts = slug_path.split('/')
                        page_dir = content_dir / '/'.join(parts[:-1]) / parts[-1]
                        page_dir.mkdir(parents=True, exist_ok=True)
                        file_path = page_dir / 'index.md'
                    else:
                        # Top-level page
                        page_dir = content_dir / slug_path
                        page_dir.mkdir(parents=True, exist_ok=True)
                        file_path = page_dir / 'index.md'
                
                # Write markdown file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                generated_files.append(str(file_path.relative_to(output_path)))
            
            # Generate hugo.toml
            config_content = self._generate_site_config()
            config_path = output_path / 'hugo.toml'
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            generated_files.append('hugo.toml')

            # --- Generate Default Layouts & Partials ---
            layouts_dir = output_path / 'layouts'
            partials_dir = layouts_dir / 'partials'
            blocks_dir = partials_dir / 'blocks'
            default_dir = layouts_dir / '_default'
            
            layouts_dir.mkdir(parents=True, exist_ok=True)
            partials_dir.mkdir(parents=True, exist_ok=True)
            blocks_dir.mkdir(parents=True, exist_ok=True)
            default_dir.mkdir(parents=True, exist_ok=True)

            # 1. _default/baseof.html
            baseof_content = """<!DOCTYPE html>
<html lang="{{ .Site.LanguageCode }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ .Title }} | {{ .Site.Title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 font-sans min-h-screen flex flex-col">
    {{ block "main" . }}{{ end }}
</body>
</html>"""
            with open(default_dir / 'baseof.html', 'w') as f: f.write(baseof_content)
            generated_files.append('layouts/_default/baseof.html')

            # 2. _default/single.html (Generic layout)
            single_content = """{{ define "main" }}
<div class="flex flex-col min-h-screen">
    {{/* Header Zone */}}
    <header class="w-full">
        {{ range .Params.header_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </header>

    <div class="container mx-auto px-4 py-8 flex-1 flex flex-col md:flex-row gap-8">
        {{/* Sidebar Zone */}}
        {{ if .Params.sidebar_blocks }}
        <aside class="w-full md:w-64 flex-shrink-0">
            {{ range .Params.sidebar_blocks }}
                {{ partial "blocks/render-block.html" . }}
            {{ end }}
        </aside>
        {{ end }}

        {{/* Main Zone */}}
        <main class="flex-1 min-w-0">
            {{ range .Params.main_blocks }}
                {{ partial "blocks/render-block.html" . }}
            {{ end }}
        </main>
    </div>

    {{/* Footer Zone */}}
    <footer class="w-full mt-auto">
        {{ range .Params.footer_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </footer>
</div>
{{ end }}"""
            with open(default_dir / 'single.html', 'w') as f: f.write(single_content)
            generated_files.append('layouts/_default/single.html')
            
            # 3. index.html (Home page - same as single for now)
            with open(layouts_dir / 'index.html', 'w') as f: f.write(single_content)
            generated_files.append('layouts/index.html')

            # 4. partials/blocks/render-block.html
            render_block_content = """{{ if .type }}
    {{ $partialPath := printf "blocks/%s.html" .type }}
    {{ if templates.Exists (printf "partials/%s" $partialPath) }}
        {{ partial $partialPath . }}
    {{ else }}
        <div class="p-4 border border-red-200 bg-red-50 text-red-700 rounded my-4">
            <strong>Missing Block Template:</strong> {{ .type }}
        </div>
    {{ end }}
{{ end }}"""
            with open(blocks_dir / 'render-block.html', 'w') as f: f.write(render_block_content)
            generated_files.append('layouts/partials/blocks/render-block.html')

            # 5. Generate basic templates for known block types
            block_templates = {
                'hero': """<section class="relative bg-slate-900 text-white py-20 px-6 rounded-lg mb-8 overflow-hidden">
    {{ if .bgImage }}<img src="{{ .bgImage }}" class="absolute inset-0 w-full h-full object-cover opacity-30">{{ end }}
    <div class="relative z-10 container mx-auto text-center">
        <h1 class="text-4xl md:text-5xl font-bold mb-4">{{ .title }}</h1>
        <p class="text-xl text-slate-300 max-w-2xl mx-auto">{{ .subtitle }}</p>
    </div>
</section>""",
                'text': """<div class="prose max-w-none mb-8">
    {{ .content | markdownify }}
</div>""",
                'markdown': """<div class="prose max-w-none mb-8">
    {{ .md | markdownify }}
</div>""",
                'image': """<figure class="mb-8">
    <img src="{{ .src }}" alt="{{ .caption }}" class="w-full h-auto rounded-lg shadow-md">
    {{ if .caption }}<figcaption class="text-center text-sm text-slate-500 mt-2">{{ .caption }}</figcaption>{{ end }}
</figure>""",
                'menu': """{{ $position := .position | default "normal" }}
{{ $isAlwaysHamburger := eq .responsive "true" }}
{{ $hamburgerDir := .hamburgerDirection | default "dropdown" }}
{{ $classes := "bg-white shadow-sm border-b border-slate-200 mb-8" }}
{{ if eq $position "overlay" }}
    {{ $classes = "absolute top-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-sm shadow-md" }}
{{ else if eq $position "fixed" }}
    {{ $classes = "fixed top-0 left-0 right-0 z-40 bg-white shadow-md" }}
{{ end }}

<nav class="{{ $classes }}">
    <div class="container mx-auto px-4">
        <div class="flex items-center justify-between h-16">
            <!-- Hamburger Button -->
            <button id="{{ if eq $hamburgerDir "sidebar" }}sidebar-menu-toggle{{ else }}dropdown-menu-toggle{{ end }}" 
                    class="{{ if not $isAlwaysHamburger }}md:hidden{{ end }} text-slate-600 hover:text-indigo-600 focus:outline-none">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
            </button>
            
            {{ if $isAlwaysHamburger }}
            <div class="text-lg font-semibold text-slate-800 ml-4">Menu</div>
            {{ end }}
            
            <!-- Desktop Links (Only visible in Standard mode on Desktop) -->
            {{ if not $isAlwaysHamburger }}
            <div class="hidden md:flex items-center space-x-2">
                {{ range .items }}
                {{ if eq $.style "pills" }}
                <a href="{{ .url }}" class="px-4 py-2 rounded-full bg-slate-100 hover:bg-indigo-100 hover:text-indigo-700 font-medium transition-colors">{{ .label }}</a>
                {{ else if eq $.style "underline" }}
                <a href="{{ .url }}" class="px-4 py-2 border-b-2 border-transparent hover:border-indigo-600 text-slate-600 font-medium transition-colors">{{ .label }}</a>
                {{ else }}
                <a href="{{ .url }}" class="px-4 py-2 text-slate-600 hover:text-indigo-600 font-medium transition-colors">{{ .label }}</a>
                {{ end }}
                {{ end }}
            </div>
            {{ end }}
        </div>
        
        <!-- Dropdown Menu Panel (Only if direction is dropdown) -->
        {{ if eq $hamburgerDir "dropdown" }}
        <div id="dropdown-menu" class="hidden pb-4">
            {{ range .items }}
            {{ if eq $.style "pills" }}
            <a href="{{ .url }}" class="block py-2 rounded-full bg-slate-100 hover:bg-indigo-100 hover:text-indigo-700 font-medium transition-colors mb-1">{{ .label }}</a>
            {{ else if eq $.style "underline" }}
            <a href="{{ .url }}" class="block py-2 border-b border-transparent hover:border-indigo-600 text-slate-600 font-medium transition-colors">{{ .label }}</a>
            {{ else }}
            <a href="{{ .url }}" class="block py-2 text-slate-600 hover:text-indigo-600 font-medium transition-colors">{{ .label }}</a>
            {{ end }}
            {{ end }}
        </div>
        {{ end }}
    </div>
</nav>

<!-- Sidebar Panel (Only if direction is sidebar) -->
{{ if eq $hamburgerDir "sidebar" }}
<!-- Sidebar overlay -->
<div id="sidebar-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden transition-opacity"></div>

<!-- Sidebar panel -->
<!-- Sidebar panel -->
<div id="sidebar-panel" class="fixed top-0 {{ if eq .sidebarSide "right" }}right-0{{ else }}left-0{{ end }} h-full w-64 bg-white shadow-xl z-50 transform {{ if eq .sidebarSide "right" }}translate-x-full{{ else }}-translate-x-full{{ end }} transition-transform duration-300 flex flex-col">
    <div class="p-4 border-b border-slate-200 flex justify-between items-center flex-shrink-0">
        <h2 class="text-lg font-semibold text-slate-800">Menu</h2>
        <button id="sidebar-close" class="text-slate-600 hover:text-indigo-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    </div>
    
    <!-- Scrollable Menu Items -->
    <div class="flex-1 overflow-y-auto p-4">
        {{ range .items }}
        {{ if eq $.style "pills" }}
        <a href="{{ .url }}" class="block py-3 px-4 rounded-full bg-slate-100 hover:bg-indigo-100 hover:text-indigo-700 font-medium transition-colors mb-2">{{ .label }}</a>
        {{ else if eq $.style "underline" }}
        <a href="{{ .url }}" class="block py-3 px-4 border-b border-transparent hover:border-indigo-600 text-slate-600 font-medium transition-colors mb-1">{{ .label }}</a>
        {{ else }}
        <a href="{{ .url }}" class="block py-3 px-4 text-slate-600 hover:text-indigo-600 hover:bg-slate-50 rounded font-medium transition-colors mb-1">{{ .label }}</a>
        {{ end }}
        {{ end }}
    </div>

    <!-- Sticky Footer -->
    {{ if $.sidebarFooterBlocks }}
    <div class="p-4 border-t border-slate-200 bg-slate-50 flex-shrink-0">
        {{ range $.sidebarFooterBlocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </div>
    {{ end }}
</div>

<script>
(function() {
    const toggle = document.getElementById('sidebar-menu-toggle');
    const overlay = document.getElementById('sidebar-overlay');
    const panel = document.getElementById('sidebar-panel');
    const close = document.getElementById('sidebar-close');
    
    if (toggle && overlay && panel) {
        const open = function() {
            overlay.classList.remove('hidden');
            panel.classList.remove('{{ if eq .sidebarSide "right" }}translate-x-full{{ else }}-translate-x-full{{ end }}');
            panel.classList.add('translate-x-0');
        };
        
        const closeMenu = function() {
            overlay.classList.add('hidden');
            panel.classList.add('{{ if eq .sidebarSide "right" }}translate-x-full{{ else }}-translate-x-full{{ end }}');
            panel.classList.remove('translate-x-0');
        };
        
        toggle.addEventListener('click', open);
        if (close) close.addEventListener('click', closeMenu);
        overlay.addEventListener('click', closeMenu);
    }
})();
</script>
{{ else }}
<!-- Dropdown Script -->
<script>
    (function() {
        const toggle = document.getElementById('dropdown-menu-toggle');
        const menu = document.getElementById('dropdown-menu');
        if (toggle && menu) {
            toggle.addEventListener('click', function() {
                menu.classList.toggle('hidden');
            });
        }
    })();
</script>
{{ end }}""",
                'flex_columns': """{{ $widths := split (.col_widths | default "100") "," }}
<div class="grid grid-cols-1 md:grid-cols-{{ len $widths }} gap-6 mb-8">
    {{ range $index, $width := $widths }}
        {{ $colKey := printf "col_%d" $index }}
        <div class="flex flex-col gap-4">
            {{/* Access the dynamic column key from the parent context */}}
            {{ $colData := index $ $colKey }}
            {{ if $colData }}
                {{ range $colData }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            {{ end }}
        </div>
    {{ end }}
</div>""",
                'youtube': """<div class="mb-8">
    <div class="aspect-w-16 aspect-h-9 relative" style="padding-bottom: 56.25%;">
        <iframe 
            class="absolute inset-0 w-full h-full rounded-lg shadow-md"
            src="https://www.youtube.com/embed/{{ .videoId }}"
            title="{{ .title | default "YouTube video" }}"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
        </iframe>
    </div>
    {{ if .title }}
    <p class="text-center text-sm text-slate-600 mt-2">{{ .title }}</p>
    {{ end }}
</div>"""
            }

            for block_type, template_content in block_templates.items():
                with open(blocks_dir / f'{block_type}.html', 'w') as f: f.write(template_content)
                generated_files.append(f'layouts/partials/blocks/{block_type}.html')
            
            return Response({
                'success': True,
                'message': f'Successfully published {len(pages)} pages',
                'output_dir': str(output_path),
                'files': generated_files
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_page_markdown(self, page):
        """
        Generate markdown file content for a page including frontmatter and blocks.
        """
        # Get blocks for this page (page-specific blocks in main/sidebar zones)
        page_blocks = BlockInstance.objects.filter(page=page, parent=None).order_by('sort_order')
        
        # Get global blocks (header/footer blocks with page=None)
        global_blocks = BlockInstance.objects.filter(page=None, parent=None, website=page.website).order_by('sort_order')
        
        # Build frontmatter
        frontmatter = f"""+++
title = "{page.title}"
date = "{page.date or ''}"
draft = false
"""
        
        if page.description:
            frontmatter += f'description = "{page.description}"\n'
        
        if page.tags:
            tags_str = ', '.join([f'"{tag}"' for tag in page.tags])
            frontmatter += f'tags = [{tags_str}]\n'
        
        # Generate block content
        content = ""
        
        # Helper function to render blocks recursively
        def render_blocks(blocks_list, zone_name, depth=0):
            output = ""
            indent = "  " * depth
            
            for block in blocks_list:
                output += f"{indent}[[{zone_name}]]\n"
                output += f'{indent}  type = "{block.definition_id}"\n'
                
                # Render simple parameters
                params = block.params
                for key, value in params.items():
                    # Skip complex objects
                    if isinstance(value, (dict, list)):
                        continue
                    # Escape special characters for TOML
                    value_str = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                    output += f'{indent}  {key} = "{value_str}"\n'
                
                # Handle menu-specific parameters
                if block.definition_id == 'menu':
                    items = params.get('items', [])
                    if items:
                        # Use inline array of inline tables for TOML compatibility
                        items_toml = "["
                        for i, item in enumerate(items):
                            if i > 0:
                                items_toml += ", "
                            label = str(item.get("label", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            url = str(item.get("url", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            item_type = str(item.get("type", "page")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            items_toml += f'{{label = "{label}", url = "{url}", type = "{item_type}"}}'
                        items_toml += "]\n"
                        output += f'{indent}  items = {items_toml}'
                    
                    # Render sidebar footer blocks
                    footer_blocks = params.get('sidebarFooterBlocks', [])
                    if footer_blocks:
                        # Use inline array of inline tables for TOML compatibility
                        footer_toml = "["
                        for i, fb in enumerate(footer_blocks):
                            if i > 0:
                                footer_toml += ", "
                            
                            # Construct the inline table for this block
                            fb_type = str(fb.get("type", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            block_str = f'{{type = "{fb_type}"'
                            
                            for k, v in fb.get('params', {}).items():
                                if not isinstance(v, (dict, list)):
                                    v_str = str(v).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                                    block_str += f', {k} = "{v_str}"'
                            
                            block_str += "}"
                            footer_toml += block_str
                        
                        footer_toml += "]\n"
                        output += f'{indent}  sidebarFooterBlocks = {footer_toml}'
                
                # Handle theme_features-specific parameters
                if block.definition_id == 'theme_features':
                    items = params.get('items', [])
                    if items:
                        items_toml = "["
                        for i, item in enumerate(items):
                            if i > 0:
                                items_toml += ", "
                            icon = str(item.get("icon", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            text = str(item.get("text", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            items_toml += f'{{icon = "{icon}", text = "{text}"}}'
                        items_toml += "]\n"
                        output += f'{indent}  items = {items_toml}'
                
                # Handle nested children (columns)
                children = block.children.all().order_by('sort_order')
                if children.exists():
                    output += render_blocks(children, f'{zone_name}.children', depth + 1)
                
                output += "\n"
            
            return output
        
        # Render blocks from different zones
        # Use flat naming convention to avoid TOML nesting issues and reserved words
        for zone in ['header', 'main', 'sidebar', 'footer']:
            if zone in ['header', 'footer']:
                # Global blocks (page=None)
                zone_blocks = global_blocks.filter(placement_key=zone)
            else:
                # Page-specific blocks (main/sidebar)
                zone_blocks = page_blocks.filter(placement_key=zone)
                
            if zone_blocks.exists():
                content += render_blocks(zone_blocks, f'{zone}_blocks')
        
        # Close frontmatter
        return frontmatter + content + "+++\n"
    
    def _generate_site_config(self):
        """
        Generate hugo.toml configuration file.
        """
        config = """baseURL = "https://example.com/"
languageCode = "en-us"
title = "My Hugo Site"

[params]
  description = "A site built with Hugo CMS"
"""
        return config