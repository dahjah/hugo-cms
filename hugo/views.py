from django.shortcuts import render
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from pathlib import Path
import uuid 
from .models import Website, Page, BlockDefinition, BlockInstance, SiteTemplate, TemplateCategory, LayoutTemplate, UploadedFile, StorageSettings
from .deployment_models import DeploymentProvider, DeploymentHistory
from .deployment_service import CloudflareR2Deployer, HugoBuilder, DeploymentOrchestrator
from django.utils import timezone
from .serializers import (
    PageListSerializer, 
    PageDetailSerializer, 
    BlockDefinitionSerializer, 
    BlockInstanceSerializer,
    SiteConfigSerializer,
    WebsiteSerializer,
    UploadedFileSerializer,
    StorageSettingsSerializer,
    DeploymentProviderSerializer
)
from .importer import import_hugo_theme_structure

def editor_view(request, website_id=None):
    """Serves the Vue.js frontend application."""
    return render(request, 'hugo/index.html', {'website_id': website_id})
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
            import shutil
            if content_dir.exists():
                shutil.rmtree(content_dir)
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all pages for this website
            if request.data.get('website_id'):
                pages = Page.objects.filter(website_id=request.data.get('website_id'))
            else:
                pages = Page.objects.all()
            generated_files = []
            
            # Get base URL for absolute image paths
            # base_url = request.build_absolute_uri('/')
            base_url = ""
            
            for page in pages:
                # Generate markdown content for this page
                markdown_content = self._generate_page_markdown(page, base_url)
                
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
                
                # Update last_published_at timestamp
                from django.utils import timezone
                page.last_published_at = timezone.now()
                page.save(update_fields=['last_published_at'])
                
                generated_files.append(str(file_path.relative_to(output_path)))
            
            # Generate hugo.toml
            config_content = self._generate_site_config(website)
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
    <link rel="stylesheet" href="/css/custom.css">
</head>
<body class="bg-slate-50 text-slate-800 font-sans min-h-screen flex flex-col">
    {{ block "main" . }}{{ end }}
</body>
</html>"""
            with open(default_dir / 'baseof.html', 'w') as f: f.write(baseof_content)
            generated_files.append('layouts/_default/baseof.html')

            # Write custom.css
            static_dir = output_path / 'static'
            css_dir = static_dir / 'css'
            css_dir.mkdir(parents=True, exist_ok=True)
            
            custom_css_path = css_dir / 'custom.css'
            with open(custom_css_path, 'w') as f:
                f.write(website.custom_css or "/* Custom CSS */")
            generated_files.append('static/css/custom.css')

            # Copy website media to static/media/uploads/{slug}
            media_src = Path(settings.MEDIA_ROOT) / 'uploads' / website.slug
            if media_src.exists():
                media_dst = static_dir / 'media' / 'uploads' / website.slug
                media_dst.mkdir(parents=True, exist_ok=True)
                import shutil
                # Copy entire directory content
                for item in media_src.glob('*'):
                    if item.is_file():
                        shutil.copy2(item, media_dst)
                generated_files.append(f"static/media/uploads/{website.slug}/")

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
            
            # 3. list.html (for homepage and list pages - respects layout parameter)
            # This template checks the layout parameter and renders blocks accordingly
            # Since we can't dynamically include templates, we check the layout value
            list_content = """{{ define "main" }}
{{ $layout := .Params.layout | default "list" }}
<div class="flex flex-col min-h-screen">
    {{/* Header Zone */}}
    <header class="w-full">
        {{ range .Params.header_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </header>
    
    {{ if eq $layout "rightsidebar" }}
        {{/* Right Sidebar Layout */}}
        <div class="container mx-auto px-4 py-8 flex-1 flex flex-col md:flex-row gap-8">
            {{/* Main Zone (left) */}}
            <main class="flex-1 min-w-0 min-h-[400px]">
                {{ range .Params.main_blocks }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            </main>
            {{/* Sidebar Zone (right) */}}
            {{ if .Params.sidebar_blocks }}
            <aside class="w-64 flex-shrink-0 border-r border-slate-100 bg-slate-50/30">
                {{ range .Params.sidebar_blocks }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            </aside>
            {{ end }}
        </div>
    {{ else }}
        {{/* Default/List Layout (sidebar on left) */}}
        <div class="container mx-auto px-4 py-8 flex-1 flex flex-col md:flex-row gap-8">
            {{/* Sidebar Zone (left) */}}
            {{ if .Params.sidebar_blocks }}
            <aside class="w-full md:w-64 flex-shrink-0">
                {{ range .Params.sidebar_blocks }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            </aside>
            {{ end }}
            {{/* Main Zone (right) */}}
            <main class="flex-1 min-w-0">
                {{ range .Params.main_blocks }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            </main>
        </div>
    {{ end }}
    
    {{/* Footer Zone */}}
    <footer class="w-full mt-auto">
        {{ range .Params.footer_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </footer>
</div>
{{ end }}"""
            with open(default_dir / 'list.html', 'w') as f: f.write(list_content)
            generated_files.append('layouts/_default/list.html')

            # 4. partials/blocks/render-block.html (removed hardcoded index.html to allow layout parameter)
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
                'hero': """<div class="relative overflow-hidden mb-8 {{ .css_classes }}">
    {{ if .bgImage }}
    <img src="{{ .bgImage }}" alt="{{ .title }}" class="w-full h-64 md:h-96 object-cover" loading="eager">
    {{ else }}
    <div class="w-full h-64 md:h-96 bg-gradient-to-r from-indigo-600 to-purple-600"></div>
    {{ end }}
    <div class="absolute inset-0 bg-black/40 flex flex-col items-center justify-center text-center px-4">
        <h1 class="text-3xl md:text-5xl font-bold text-white mb-4 drop-shadow-lg">{{ .title }}</h1>
        {{ if .subtitle }}
        <p class="text-lg md:text-xl text-white/90 max-w-2xl drop-shadow">{{ .subtitle }}</p>
        {{ end }}
    </div>
</div>""",
                'text': """<div class="prose max-w-none mb-8 {{ .css_classes }}">
    {{ .content | safeHTML }}
</div>""",
                'markdown': """<div class="prose max-w-none mb-8 {{ .css_classes }}">
    {{ .md | markdownify }}
</div>""",
                'html': """<div class="html-block mb-8 {{ .css_classes }}">
    {{ .html | safeHTML }}
</div>""",
                'image': """<figure class="mb-8 {{ .css_classes }}" style="width: {{ .width | default "100%" }}; margin: 0 auto;">
    <img src="{{ .src }}" alt="{{ .caption }}" class="w-full rounded-lg shadow-md" style="height: {{ .height | default "auto" }}; object-fit: cover;">
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

<nav class="{{ $classes }} {{ .css_classes }}">
    <div class="container mx-auto px-4">
        <div class="flex items-center justify-between h-16">
            <!-- Hamburger Button -->
            <button id="{{ if eq $hamburgerDir "sidebar" }}sidebar-menu-toggle{{ else }}dropdown-menu-toggle{{ end }}" 
                    class="{{ if not $isAlwaysHamburger }}md:hidden{{ end }} text-slate-600 hover:text-indigo-600 focus:outline-none">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
            </button>
            
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
<div class="grid grid-cols-1 md:grid-cols-{{ len $widths }} gap-6 mb-8 {{ .css_classes }}">
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
                'brand_logo': """
{{ $logoSize := .logo_size | default "80" }}
{{ $linkUrl := .link_url | default "/" }}
<a class="brand-logo inline-flex items-center gap-2 no-underline transition-opacity hover:opacity-85 {{ .css_classes }}" href="{{ $linkUrl }}">
    {{ if .logo_image }}
    <img src="{{ .logo_image }}" alt="{{ .brand_name }}" class="logo-icon" style="width: {{ $logoSize }}px; height: {{ $logoSize }}px; object-fit: contain;">
    {{ end }}
    <div class="logo-text flex flex-col gap-0.5">
        {{ if .brand_name }}
        <div class="brand-name font-serif font-bold text-xl text-slate-800" style="line-height: 1.2;">{{ .brand_name }}</div>
        {{ end }}
        {{ if .tagline }}
        <div class="brand-tagline text-xs text-slate-500 tracking-wider uppercase font-medium" style="line-height: 1;">{{ .tagline }}</div>
        {{ end }}
    </div>
</a>""",
                'button': """
{{ $style := .style | default "primary" }}
{{ $size := .size | default "medium" }}
{{ $fullWidth := .full_width | default false }}
{{ $newTab := .new_tab | default false }}

{{ $baseClasses := "inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 no-underline" }}

{{ $sizeClasses := "" }}
{{ if eq $size "small" }}
    {{ $sizeClasses = "px-4 py-2 text-sm" }}
{{ else if eq $size "large" }}
    {{ $sizeClasses = "px-8 py-4 text-lg" }}
{{ else }}
    {{ $sizeClasses = "px-6 py-3 text-base" }}
{{ end }}

{{ $styleClasses := "" }}
{{ if eq $style "primary" }}
    {{ $styleClasses = "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md hover:shadow-lg" }}
{{ else if eq $style "secondary" }}
    {{ $styleClasses = "bg-slate-600 text-white hover:bg-slate-700 shadow-md hover:shadow-lg" }}
{{ else if eq $style "outline" }}
    {{ $styleClasses = "border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50" }}
{{ else if eq $style "ghost" }}
    {{ $styleClasses = "text-indigo-600 hover:bg-indigo-50" }}
{{ end }}

{{ $widthClass := "" }}
{{ if $fullWidth }}
    {{ $widthClass = "w-full" }}
{{ end }}

<div class="mb-4 {{ .css_classes }}">
    <a href="{{ .url | default "#" }}" 
       class="{{ $baseClasses }} {{ $sizeClasses }} {{ $styleClasses }} {{ $widthClass }}"
       {{ if $newTab }}target="_blank" rel="noopener noreferrer"{{ end }}>
        {{ .text | default "Button" }}
    </a>
</div>""",
                'youtube': """<div class="mb-8 {{ .css_classes }}" style="width: {{ .width | default "100%" }}; margin: 0 auto;">
    <div class="aspect-w-16 aspect-h-9 relative" style="padding-bottom: {{ if eq .aspect_ratio "4/3" }}75%{{ else }}56.25%{{ end }};">
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
</div>""",
                'quote': """<blockquote class="border-l-4 border-indigo-500 pl-4 py-2 mb-8 italic text-slate-700 {{ .css_classes }}">
    <p class="text-lg">{{ .text }}</p>
    {{ if .author }}
    <footer class="text-sm text-slate-500 mt-2 not-italic">— {{ .author }}</footer>
    {{ end }}
</blockquote>""",
                'alert': """{{ $alertType := .alert_type | default "info" }}
<div class="border-l-4 p-4 mb-8 rounded {{ .css_classes }} {{ if eq $alertType "success" }}border-green-500 bg-green-50{{ else if eq $alertType "warning" }}border-yellow-500 bg-yellow-50{{ else if eq $alertType "error" }}border-red-500 bg-red-50{{ else }}border-blue-500 bg-blue-50{{ end }}">
    <div class="flex items-start">
        <div class="flex-shrink-0">
            {{ if eq $alertType "success" }}
            <svg class="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            {{ else if eq $alertType "warning" }}
            <svg class="h-5 w-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            {{ else if eq $alertType "error" }}
            <svg class="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            {{ else }}
            <svg class="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
            {{ end }}
        </div>
        <div class="ml-3 flex-1">
            {{ if .title }}
            <h3 class="text-sm font-medium {{ if eq $alertType "success" }}text-green-900{{ else if eq $alertType "warning" }}text-yellow-900{{ else if eq $alertType "error" }}text-red-900{{ else }}text-blue-900{{ end }}">{{ .title }}</h3>
            {{ end }}
            <div class="text-sm {{ if eq $alertType "success" }}text-green-900{{ else if eq $alertType "warning" }}text-yellow-900{{ else if eq $alertType "error" }}text-red-900{{ else }}text-blue-900{{ end }} {{ if .title }}mt-2{{ end }}">
                {{ .message | safeHTML }}
            </div>
        </div>
    </div>
</div>""",
                'features_grid': """
<div class="py-16 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        {{ range .features }}
        <div class="text-center p-6 rounded-lg hover:shadow-lg transition-shadow">
            {{ if .icon }}
            <div class="w-16 h-16 mx-auto mb-4 bg-indigo-100 rounded-full flex items-center justify-center">
                <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            {{ end }}
            <h4 class="text-xl font-semibold mb-3 text-slate-800">{{ .title }}</h4>
            <p class="text-slate-600">{{ .description }}</p>
        </div>
        {{ end }}
    </div>
</div>""",
                'process_steps': """
<div class="py-16 px-4 bg-slate-50 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-4xl mx-auto space-y-8">
        {{ range $index, $step := .steps }}
        <div class="flex gap-6 items-start">
            <div class="flex-shrink-0">
                <div class="w-12 h-12 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xl font-bold">
                    {{ add $index 1 }}
                </div>
            </div>
            <div class="flex-1">
                <h3 class="text-2xl font-semibold mb-2 text-slate-900">{{ .title }}</h3>
                <p class="text-slate-600 leading-relaxed">{{ .description }}</p>
            </div>
        </div>
        {{ end }}
    </div>
</div>""",
                'stats_counter': """
<div class="py-16 px-4 bg-indigo-600 text-white {{ .css_classes }}">
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
        {{ range .stats }}
        <div>
            <div class="text-5xl font-bold mb-2">{{ .value }}{{ if .suffix }}{{ .suffix }}{{ end }}</div>
            <div class="text-indigo-100 text-lg">{{ .label }}</div>
        </div>
        {{ end }}
    </div>
</div>""",
                'stats': """
<div class="py-16 px-4 bg-indigo-600 text-white {{ .css_classes }}">
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
        {{ range .items }}
        <div class="stat-item" data-animate="{{ $.animate | default true }}">
            <div class="text-5xl font-bold mb-2 stat-value">{{ .value }}{{ if .suffix }}{{ .suffix }}{{ end }}</div>
            <div class="text-indigo-100 text-lg">{{ .label }}</div>
        </div>
        {{ end }}
    </div>
</div>""",
                'menu_grid': """
<div class="py-16 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {{ range .items }}
        <div class="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-shadow">
            {{ if .image }}
            <img src="{{ .image }}" alt="{{ .name }}" class="w-full h-48 object-cover"/>
            {{ end }}
            <div class="p-4">
                <h4 class="text-lg font-semibold mb-2 text-slate-900">{{ .name }}</h4>
                {{ if .description }}
                <p class="text-sm text-slate-600">{{ .description }}</p>
                {{ end }}
            </div>
        </div>
        {{ end }}
    </div>
</div>""",
                'cta_hero': """
<div class="relative overflow-hidden {{ .css_classes }}">
    {{ if .background_image }}
    <div class="absolute inset-0 z-0">
        <img src="{{ .background_image }}" alt="Background" class="w-full h-full object-cover"/>
        <div class="absolute inset-0 bg-black/50"></div>
    </div>
    {{ end }}
    <div class="relative z-10 max-w-4xl mx-auto text-center py-24 px-4">
        {{ if .headline }}
        <h1 class="text-4xl md:text-6xl font-bold mb-6 {{ if .background_image }}text-white{{ else }}text-slate-900{{ end }}">{{ .headline }}</h1>
        {{ end }}
        {{ if .subheadline }}
        <p class="text-xl md:text-2xl mb-8 {{ if .background_image }}text-white/90{{ else }}text-slate-700{{ end }}">{{ .subheadline }}</p>
        {{ end }}
        {{ if .cta_text }}
        <a href="{{ .cta_url | default "#" }}" class="inline-block px-8 py-4 bg-indigo-600 text-white text-lg font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-lg">
            {{ .cta_text }}
        </a>
        {{ end }}
    </div>
</div>""",
                'social_links': """
<div class="py-8 {{ .css_classes }}">
    <div class="max-w-6xl mx-auto flex justify-center gap-6">
        {{ range .links }}
        <a href="{{ .url }}" target="_blank" rel="noopener noreferrer" class="w-10 h-10 flex items-center justify-center rounded-full bg-slate-700 hover:bg-indigo-600 text-white transition-colors">
            {{ if eq .platform "facebook" }}
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            {{ else if eq .platform "instagram" }}
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
            {{ else if eq .platform "twitter" }}
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
            {{ else if eq .platform "linkedin" }}
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            {{ else if eq .platform "youtube" }}
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            {{ else }}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
            {{ end }}
        </a>
        {{ end }}
    </div>
</div>""",
                'faq': """
<div class="py-16 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-3xl mx-auto space-y-4">
        {{ range $index, $item := .questions }}
        <details class="group bg-white rounded-lg shadow-md overflow-hidden">
            <summary class="cursor-pointer p-6 font-semibold text-slate-900 hover:bg-slate-50 transition-colors flex items-center justify-between">
                <span>{{ .question }}</span>
                <svg class="w-5 h-5 text-slate-500 transform transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </summary>
            <div class="px-6 pb-6 text-slate-600 border-t border-slate-100 pt-4">
                {{ .answer }}
            </div>
        </details>
        {{ end }}
    </div>
</div>""",
                'google_reviews': """
<div class="py-16 px-4 bg-slate-50 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-4 text-slate-900">{{ .title }}</h2>
    {{ end }}
    {{ if .subtitle }}
    <p class="text-center text-slate-600 mb-12 max-w-2xl mx-auto">{{ .subtitle }}</p>
    {{ end }}
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {{ range .reviews }}
        <div class="bg-white rounded-lg shadow-md p-6 flex flex-col">
            <div class="flex items-start mb-4">
                {{ if .image }}
                <img src="{{ .image }}" alt="{{ .name }}" class="w-12 h-12 rounded-full mr-3 object-cover">
                {{ else }}
                <div class="w-12 h-12 rounded-full mr-3 bg-indigo-100 flex items-center justify-center text-indigo-600 font-semibold">
                    {{ substr .name 0 1 }}
                </div>
                {{ end }}
                <div class="flex-1">
                    <h4 class="font-semibold text-slate-900">{{ .name }}</h4>
                    <div class="flex items-center gap-1 mt-1">
                        {{ range seq (int .rating) }}
                        <svg class="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 20 20">
                            <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                        </svg>
                        {{ end }}
                        {{ range seq (sub 5 (int .rating)) }}
                        <svg class="w-4 h-4 text-slate-300 fill-current" viewBox="0 0 20 20">
                            <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                        </svg>
                        {{ end }}
                    </div>
                </div>
            </div>
            <p class="text-slate-600 text-sm flex-1 mb-3">{{ .text }}</p>
            {{ if .date }}
            <p class="text-xs text-slate-400">{{ .date }}</p>
            {{ end }}
        </div>
        {{ end }}
    </div>
</div>""",
                'flip_cards': """
<div class="py-8 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-8 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {{ range .cards }}
        <div class="group perspective-1000 h-64 cursor-pointer">
            <div class="relative w-full h-full transition-transform duration-500 transform-style-preserve-3d group-hover:rotate-y-180">
                <!-- Front -->
                <div class="absolute inset-0 backface-hidden bg-white rounded-lg shadow-md p-6 flex flex-col items-center justify-center text-center">
                    {{ if .front_icon }}
                    <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 mb-4">
                        <i data-lucide="{{ .front_icon }}" class="w-8 h-8"></i>
                    </div>
                    {{ end }}
                    <h3 class="text-xl font-semibold text-slate-800">{{ .front_title }}</h3>
                </div>
                <!-- Back -->
                <div class="absolute inset-0 backface-hidden rotate-y-180 bg-indigo-600 rounded-lg shadow-md p-6 flex flex-col items-center justify-center text-center text-white">
                    <p class="mb-4">{{ .back_description }}</p>
                    {{ if .back_cta_text }}
                    <a href="{{ .back_cta_url | default "#" }}" class="px-4 py-2 bg-white text-indigo-600 rounded-full text-sm font-bold hover:bg-indigo-50 transition-colors">
                        {{ .back_cta_text }}
                    </a>
                    {{ end }}
                </div>
            </div>
        </div>
        {{ end }}
    </div>
</div>
<style>
.perspective-1000 { perspective: 1000px; }
.transform-style-preserve-3d { transform-style: preserve-3d; }
.backface-hidden { backface-visibility: hidden; }
.rotate-y-180 { transform: rotateY(180deg); }
.group:hover .group-hover\\:rotate-y-180 { transform: rotateY(180deg); }
</style>""",
                'accordion': """
<div class="py-8 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-8 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-3xl mx-auto space-y-4">
        {{ range $index, $item := .items }}
        <details class="group bg-white rounded-lg shadow-md overflow-hidden" {{ if eq $index 0 }}open{{ end }}>
            <summary class="cursor-pointer p-6 font-semibold text-slate-900 hover:bg-slate-50 transition-colors flex items-center justify-between list-none">
                <span>{{ .title }}</span>
                <svg class="w-5 h-5 text-slate-500 transform transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </summary>
            <div class="px-6 pb-6 text-slate-600 border-t border-slate-100 pt-4">
                {{ .content | safeHTML }}
            </div>
        </details>
        {{ end }}
    </div>
</div>""",
                'carousel': """
{{ $autoAdvance := .auto_advance | default false }}
{{ $interval := .interval_seconds | default 5 }}
{{ $showDots := .show_dots | default true }}
{{ $showArrows := .show_arrows | default true }}
{{ $uniqueId := .id | default (now.UnixNano | printf "%d") }}

<div class="carousel-container py-8 {{ .css_classes }}" 
     data-carousel-id="{{ $uniqueId }}"
     data-auto-advance="{{ $autoAdvance }}"
     data-interval="{{ $interval }}">
    
    <!-- Carousel Wrapper -->
    <div class="relative" style="display: grid; grid-template-areas: 'stack'; place-items: center; min-height: 300px; overflow: hidden;">
        {{ range $index, $block := .blocks }}
        <div class="carousel-slide" 
             data-slide-index="{{ $index }}"
             style="grid-area: stack; width: 85%; max-width: 900px; transition: transform 0.5s ease-in-out, opacity 0.5s ease-in-out; {{ if eq $index 0 }}transform: translateX(0); opacity: 1;{{ else }}transform: translateX(100%); opacity: 0; pointer-events: none;{{ end }}">
             {{ partial "blocks/render-block.html" $block }}
        </div>
        {{ end }}
        
        {{ if not .blocks }}
        <div class="py-16 px-8 flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 text-slate-400 rounded-lg">
            No slides added
        </div>
        {{ end }}
        
        <!-- Arrows -->
        {{ if and $showArrows .blocks (gt (len .blocks) 1) }}
        <button data-carousel-prev
                style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); z-index: 10;"
                class="w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all bg-slate-100/80 hover:bg-slate-200 border border-slate-200 backdrop-blur">
            <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
        </button>
        <button data-carousel-next
                style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); z-index: 10;"
                class="w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all bg-slate-100/80 hover:bg-slate-200 border border-slate-200 backdrop-blur">
            <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
        </button>
        {{ end }}
    </div>
    
    <!-- Dots -->
    {{ if and $showDots .blocks (gt (len .blocks) 1) }}
    <div class="flex justify-center gap-3 mt-6">
        {{ range $index, $block := .blocks }}
        <button data-carousel-dot="{{ $index }}"
                class="transition-all duration-200 border-0 cursor-pointer p-0"
                style="{{ if eq $index 0 }}width: 32px; border-radius: 6px; background: var(--color-primary, #6366f1);{{ else }}width: 12px; border-radius: 50%; background: #e2e8f0;{{ end }} height: 12px;">
        </button>
        {{ end }}
    </div>
    {{ end }}
</div>

<script>
(function() {
    const carousel = document.querySelector('[data-carousel-id="{{ $uniqueId }}"]');
    if (!carousel) return;
    
    const slides = carousel.querySelectorAll('.carousel-slide');
    const dots = carousel.querySelectorAll('[data-carousel-dot]');
    const prevBtn = carousel.querySelector('[data-carousel-prev]');
    const nextBtn = carousel.querySelector('[data-carousel-next]');
    const autoAdvance = carousel.dataset.autoAdvance === 'true';
    const interval = parseInt(carousel.dataset.interval) || 5;
    
    if (slides.length <= 1) return;
    
    let currentSlide = 0;
    let autoAdvanceTimer = null;
    
    function goToSlide(index) {
        slides.forEach((slide, i) => {
            if (i === index) {
                slide.style.transform = 'translateX(0)';
                slide.style.opacity = '1';
                slide.style.pointerEvents = 'auto';
            } else if (i < index) {
                slide.style.transform = 'translateX(-100%)';
                slide.style.opacity = '0';
                slide.style.pointerEvents = 'none';
            } else {
                slide.style.transform = 'translateX(100%)';
                slide.style.opacity = '0';
                slide.style.pointerEvents = 'none';
            }
        });
        
        dots.forEach((dot, i) => {
            if (i === index) {
                dot.style.width = '32px';
                dot.style.borderRadius = '6px';
                dot.style.background = 'var(--color-primary, #6366f1)';
            } else {
                dot.style.width = '12px';
                dot.style.borderRadius = '50%';
                dot.style.background = '#e2e8f0';
            }
        });
        
        currentSlide = index;
        resetTimer();
    }
    
    function nextSlide() {
        goToSlide((currentSlide + 1) % slides.length);
    }
    
    function prevSlide() {
        goToSlide((currentSlide - 1 + slides.length) % slides.length);
    }
    
    function resetTimer() {
        if (autoAdvanceTimer) clearInterval(autoAdvanceTimer);
        if (autoAdvance) {
            autoAdvanceTimer = setInterval(nextSlide, interval * 1000);
        }
    }
    
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    dots.forEach((dot, i) => dot.addEventListener('click', () => goToSlide(i)));
    
    carousel.addEventListener('mouseenter', () => {
        if (autoAdvanceTimer) clearInterval(autoAdvanceTimer);
    });
    carousel.addEventListener('mouseleave', resetTimer);
    
    resetTimer();
})();
</script>""",
                'testimonials': """<div class="testimonials {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>""",
                'testimonial': """
<div class="testimonial {{ .css_classes }}">
    <div class="testimonial-quote">{{ .quote }}</div>
    {{ if .author }}
    <div class="testimonial-author">{{ .author }}</div>
    {{ end }}
</div>""",
                'section': """
{{ $style := .style | default "welcome" }}
<div class="section-{{ $style }} {{ .css_classes }}">
    <div class="container">
        {{ range .blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </div>
</div>""",
                'two_col': """
{{ $ratio := .ratio | default "50-50" }}
{{ $reverse := .reverse | default false }}
<div class="two-col col-{{ $ratio }}{{ if $reverse }} reverse{{ end }} {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>""",
                'row': """
{{ $justify := .justify | default "start" }}
{{ $align := .align | default "stretch" }}
{{ $gap := .gap | default "4" }}

{{ $justifyClass := "" }}
{{ if eq $justify "start" }}{{ $justifyClass = "justify-start" }}{{ end }}
{{ if eq $justify "center" }}{{ $justifyClass = "justify-center" }}{{ end }}
{{ if eq $justify "end" }}{{ $justifyClass = "justify-end" }}{{ end }}
{{ if eq $justify "between" }}{{ $justifyClass = "justify-between" }}{{ end }}
{{ if eq $justify "around" }}{{ $justifyClass = "justify-around" }}{{ end }}
{{ if eq $justify "evenly" }}{{ $justifyClass = "justify-evenly" }}{{ end }}

{{ $alignClass := "" }}
{{ if eq $align "start" }}{{ $alignClass = "items-start" }}{{ end }}
{{ if eq $align "center" }}{{ $alignClass = "items-center" }}{{ end }}
{{ if eq $align "end" }}{{ $alignClass = "items-end" }}{{ end }}
{{ if eq $align "stretch" }}{{ $alignClass = "items-stretch" }}{{ end }}

<div class="flex flex-wrap gap-{{ $gap }} mb-8 {{ $justifyClass }} {{ $alignClass }} {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>""",
                'col': """
<div class="{{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>""",
                'column': """
<div class="flex flex-col gap-4 {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>""",
                'theme_features': """
<div class="py-16 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        {{ range .items }}
        <div class="text-center p-6 rounded-lg hover:shadow-lg transition-shadow bg-white">
            {{ if .icon }}
            <div class="w-16 h-16 mx-auto mb-4 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            {{ end }}
            <h4 class="text-xl font-semibold mb-3 text-slate-800">{{ .title }}</h4>
            <p class="text-slate-600">{{ .description }}</p>
        </div>
        {{ end }}
    </div>
</div>""",
                'stats': """
<div class="py-12 bg-white {{ .css_classes }}">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {{ range .items }}
            <div class="p-6">
                <div class="text-4xl font-extrabold text-indigo-600 mb-2">
                    {{ .value }}<span class="text-2xl ml-1 text-indigo-400">{{ .suffix }}</span>
                </div>
                <div class="text-sm font-semibold text-slate-500 uppercase tracking-wider">{{ .label }}</div>
            </div>
            {{ end }}
        </div>
    </div>
</div>""",
                'embed': """
<div class="w-full my-8 {{ .css_classes }}">
    {{ if eq .embed_type "iframe" }}
    <div class="relative w-full overflow-hidden rounded-lg shadow-lg border border-slate-200" style="height: {{ .height | default "400" }}px;">
        <iframe src="{{ .src }}" title="{{ .title }}" class="absolute top-0 left-0 w-full h-full border-0" allowfullscreen></iframe>
    </div>
    {{ else }}
    <div class="w-full flex justify-center">
        {{ .src | safeHTML }}
    </div>
    {{ end }}
</div>"""
            }

            for block_type, template_content in block_templates.items():
                with open(blocks_dir / f'{block_type}.html', 'w') as f: f.write(template_content)
                generated_files.append(f'layouts/partials/blocks/{block_type}.html')
            
            # 6. Generate layout-specific templates for each LayoutTemplate
            layout_files = self._generate_layout_templates(layouts_dir, default_dir)
            generated_files.extend(layout_files)
            
            # 7. Deploy if provider is configured
            if request.data.get('website_id'):
                try:
                    website = Website.objects.get(id=request.data.get('website_id'))
                    if website.deployment_provider and website.deployment_provider.enabled:
                        # Use Orchestrator for full deployment pipeline
                        orchestrator = DeploymentOrchestrator(website.deployment_provider, website)
                        deployment = orchestrator.deploy(output_path)
                        
                        if deployment.status == 'success':
                            generated_files.append(f"DEPLOYMENT: Success ({deployment.deployment_url})")
                        else:
                            generated_files.append(f"DEPLOYMENT: Failed - {deployment.error_message}")
                            
                except Exception as e:
                    print(f"Deployment error: {e}")
                    generated_files.append(f"DEPLOYMENT: Error - {str(e)}")
            
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
    
    @action(detail=False, methods=['post'])
    def publish_page(self, request):
        """
        Publish a single page to Hugo output directory.
        Accepts website_id and page_id in request body.
        """
        try:
            website_id = request.data.get('website_id')
            page_id = request.data.get('page_id')
            
            if not website_id or not page_id:
                return Response({
                    'success': False,
                    'error': 'website_id and page_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                website = Website.objects.get(id=website_id)
                page = Page.objects.get(id=page_id, website=website)
            except (Website.DoesNotExist, Page.DoesNotExist) as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Build output path
            base_output_dir = Path(settings.BASE_DIR) / 'hugo_output'
            output_path = base_output_dir / website.slug
            content_dir = output_path / 'content'
            
            # Ensure content directory exists
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate base URL for absolute paths
            base_url = request.build_absolute_uri('/')
            
            # Generate markdown for this page
            page_content = self._generate_page_markdown(page, base_url)
            
            # Write to appropriate location
            if page.slug == '/':
                page_file = content_dir / '_index.md'
            else:
                page_dir = content_dir / page.slug.strip('/')
                page_dir.mkdir(parents=True, exist_ok=True)
                page_file = page_dir / 'index.md'
            
            with open(page_file, 'w') as f:
                f.write(page_content)
            
            # Update last_published_at timestamp
            from django.utils import timezone
            page.last_published_at = timezone.now()
            page.save(update_fields=['last_published_at'])
            
            return Response({
                'success': True,
                'message': f'Successfully published page: {page.title}',
                'file': str(page_file)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_layout_templates(self, layouts_dir, default_dir):
        """
        Generate Hugo layout templates for each LayoutTemplate in the database.
        Each template respects the zones configuration (order, width, cssClasses).
        Generates templates in both _default/ and type-specific directories for homepage support.
        """
        from .models import LayoutTemplate
        generated_files = []
        
        layouts = LayoutTemplate.objects.all()
        
        for layout in layouts:
            # Sort zones by order
            zones = sorted(layout.zones, key=lambda z: z.get('order', 0))
            
            # Build the template content
            template_parts = []
            template_parts.append('{{ define "main" }}')
            template_parts.append('<div class="flex flex-col min-h-screen">')
            
            # Group zones by their width type to handle flex containers
            full_width_zones = [z for z in zones if z.get('width') == 'w-full']
            flex_zones = [z for z in zones if z.get('width') != 'w-full']
            
            # Render full-width zones in order, with flex zones in a container
            current_order = 0
            
            for zone in zones:
                zone_name = zone.get('name', 'main')
                zone_width = zone.get('width', 'flex-1')
                zone_css = zone.get('cssClasses', '')
                zone_order = zone.get('order', 0)
                
                if zone_width == 'w-full':
                    # Full-width zone (header/footer)
                    if zone_name == 'header':
                        template_parts.append(f'    {{{{/* Header Zone */}}}}')
                        template_parts.append(f'    <header class="w-full {zone_css}">')
                        template_parts.append(f'        {{{{ range .Params.{zone_name}_blocks }}}}')
                        template_parts.append(f'            {{{{ partial "blocks/render-block.html" . }}}}')
                        template_parts.append(f'        {{{{ end }}}}')
                        template_parts.append(f'    </header>')
                    elif zone_name == 'footer':
                        template_parts.append(f'    {{{{/* Footer Zone */}}}}')
                        template_parts.append(f'    <footer class="w-full mt-auto {zone_css}">')
                        template_parts.append(f'        {{{{ range .Params.{zone_name}_blocks }}}}')
                        template_parts.append(f'            {{{{ partial "blocks/render-block.html" . }}}}')
                        template_parts.append(f'        {{{{ end }}}}')
                        template_parts.append(f'    </footer>')
                    else:
                        template_parts.append(f'    <div class="w-full {zone_css}">')
                        template_parts.append(f'        {{{{ range .Params.{zone_name}_blocks }}}}')
                        template_parts.append(f'            {{{{ partial "blocks/render-block.html" . }}}}')
                        template_parts.append(f'        {{{{ end }}}}')
                        template_parts.append(f'    </div>')
                
                # Check if we need to start a flex container for non-full-width zones
                elif zone_order > current_order and any(z.get('order', 0) > current_order and z.get('width') != 'w-full' for z in zones):
                    # This is the first flex zone, start container
                    if current_order == 0 or (current_order > 0 and zones[current_order-1].get('width') == 'w-full'):
                        template_parts.append('    <div class="container mx-auto px-4 py-8 flex-1 flex flex-col md:flex-row gap-8">')
                    
                    # Render flex zones
                    for flex_zone in [z for z in zones if z.get('order', 0) >= zone_order and z.get('width') != 'w-full']:
                        fz_name = flex_zone.get('name', 'main')
                        fz_width = flex_zone.get('width', 'flex-1')
                        fz_css = flex_zone.get('cssClasses', '')
                        
                        if fz_name == 'sidebar':
                            template_parts.append(f'        {{{{/* Sidebar Zone */}}}}')
                            template_parts.append(f'        {{{{ if .Params.{fz_name}_blocks }}}}')
                            template_parts.append(f'        <aside class="{fz_width} flex-shrink-0 {fz_css}">')
                            template_parts.append(f'            {{{{ range .Params.{fz_name}_blocks }}}}')
                            template_parts.append(f'                {{{{ partial "blocks/render-block.html" . }}}}')
                            template_parts.append(f'            {{{{ end }}}}')
                            template_parts.append(f'        </aside>')
                            template_parts.append(f'        {{{{ end }}}}')
                        elif fz_name == 'main':
                            template_parts.append(f'        {{{{/* Main Zone */}}}}')
                            template_parts.append(f'        <main class="{fz_width} min-w-0 {fz_css}">')
                            template_parts.append(f'            {{{{ range .Params.{fz_name}_blocks }}}}')
                            template_parts.append(f'                {{{{ partial "blocks/render-block.html" . }}}}')
                            template_parts.append(f'            {{{{ end }}}}')
                            template_parts.append(f'        </main>')
                    
                    template_parts.append('    </div>')
                    break  # Only process flex container once
            
            template_parts.append('</div>')
            template_parts.append('{{ end }}')
            
            # Write the template content
            template_content = '\n'.join(template_parts)
            
            # 1. Write to _default/{layout}.html (for regular pages with layout parameter)
            layout_file = default_dir / f'{layout.id}.html'
            with open(layout_file, 'w') as f:
                f.write(template_content)
            generated_files.append(f'layouts/_default/{layout.id}.html')
            
            # 2. Write to {layout}/list.html (for homepage with type parameter)
            # This allows homepage to use type="rightsidebar" and find layouts/rightsidebar/list.html
            type_dir = layouts_dir / layout.id
            type_dir.mkdir(parents=True, exist_ok=True)
            type_list_file = type_dir / 'list.html'
            with open(type_list_file, 'w') as f:
                f.write(template_content)
            generated_files.append(f'layouts/{layout.id}/list.html')
        
        return generated_files
    
    def _generate_page_markdown(self, page, base_url=""):
        """
        Generate markdown file content for a page including frontmatter and blocks.
        """
        # Get blocks for this page (page-specific blocks in main/sidebar zones)
        page_blocks = BlockInstance.objects.filter(page=page, parent=None).order_by('sort_order')
        
        # Get global blocks (header/footer blocks with page=None)
        global_blocks = BlockInstance.objects.filter(page=None, parent=None, website=page.website).order_by('sort_order')
        
        # Build frontmatter
        # For homepage (kind: home), Hugo prioritizes home.html over layout parameter
        # Use 'type' to override template lookup directory for homepage
        is_homepage = (page.slug == '/' or page.slug == '')
        
        frontmatter = f"""+++
title = "{page.title}"
date = "{page.date or ''}"
draft = false
"""
        
        if is_homepage:
            # For homepage, use 'type' to change template lookup directory
            # This makes Hugo look in layouts/{type}/ instead of layouts/home.html
            frontmatter += f'type = "{page.layout}"\n'
        else:
            # For other pages, use 'layout' parameter
            frontmatter += f'layout = "{page.layout}"\n'
        
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
                    # Skip 'type' to avoid duplicate key (already output as block type)
                    if key == 'type':
                        continue
                    
                    # Skip complex objects
                    if isinstance(value, (dict, list)):
                        continue
                    
                    # Prepend base_url to local media paths
                    # Convert booleans to lowercase strings for JS compatibility
                    if isinstance(value, bool):
                        # Output as unquoted TOML boolean (true/false)
                        value_toml = "true" if value else "false"
                        output += f'{indent}  {key} = {value_toml}\n'
                    else:
                        value_str = str(value)
                        if value_str.startswith(settings.MEDIA_URL):
                            value_str = f"{base_url.rstrip('/')}{value_str}"
                            
                        # Escape special characters for TOML
                        value_str = value_str.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
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
                                    v_str = str(v)
                                    if v_str.startswith(settings.MEDIA_URL):
                                        v_str = f"{base_url.rstrip('/')}{v_str}"
                                    v_str = v_str.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
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
                
                # Handle features_grid-specific parameters
                if block.definition_id == 'features_grid':
                    items = params.get('items', [])
                    if items:
                        items_toml = "["
                        for i, item in enumerate(items):
                            if i > 0:
                                items_toml += ", "
                            icon = str(item.get("icon", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            title = str(item.get("title", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            description = str(item.get("description", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            items_toml += f'{{icon = "{icon}", title = "{title}", description = "{description}"}}'
                        items_toml += "]\n"
                        output += f'{indent}  items = {items_toml}'
                
                # Handle process_steps-specific parameters
                if block.definition_id == 'process_steps':
                    steps = params.get('steps', [])
                    if steps:
                        steps_toml = "["
                        for i, step in enumerate(steps):
                            if i > 0:
                                steps_toml += ", "
                            title = str(step.get("title", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            description = str(step.get("description", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            steps_toml += f'{{title = "{title}", description = "{description}"}}'
                        steps_toml += "]\n"
                        output += f'{indent}  steps = {steps_toml}'
                
                # Handle stats-specific parameters (new canonical block)
                if block.definition_id == 'stats':
                    items = params.get('items', [])
                    if items:
                        items_toml = "["
                        for i, item in enumerate(items):
                            if i > 0:
                                items_toml += ", "
                            value = str(item.get("value", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            suffix = str(item.get("suffix", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            label = str(item.get("label", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            items_toml += f'{{value = "{value}", suffix = "{suffix}", label = "{label}"}}'
                        items_toml += "]\n"
                        output += f'{indent}  items = {items_toml}'
                
                # Handle stats_counter-specific parameters (legacy block)
                if block.definition_id == 'stats_counter':
                    stats = params.get('stats', [])
                    if stats:
                        stats_toml = "["
                        for i, stat in enumerate(stats):
                            if i > 0:
                                stats_toml += ", "
                            value = str(stat.get("value", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            suffix = str(stat.get("suffix", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            label = str(stat.get("label", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            stats_toml += f'{{value = "{value}", suffix = "{suffix}", label = "{label}"}}'
                        stats_toml += "]\n"
                        output += f'{indent}  stats = {stats_toml}'
                
                # Handle menu_grid-specific parameters
                if block.definition_id == 'menu_grid':
                    items = params.get('items', [])
                    if items:
                        items_toml = "["
                        for i, item in enumerate(items):
                            if i > 0:
                                items_toml += ", "
                            name = str(item.get("name", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            image = str(item.get("image", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            description = str(item.get("description", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            items_toml += f'{{name = "{name}", image = "{image}", description = "{description}"}}'
                        items_toml += "]\n"
                        output += f'{indent}  items = {items_toml}'
                
                # Handle social_links-specific parameters
                if block.definition_id == 'social_links':
                    links = params.get('links', [])
                    if links:
                        links_toml = "["
                        for i, link in enumerate(links):
                            if i > 0:
                                links_toml += ", "
                            platform = str(link.get("platform", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            url = str(link.get("url", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            links_toml += f'{{platform = "{platform}", url = "{url}"}}'
                        links_toml += "]\n"
                        output += f'{indent}  links = {links_toml}'
                
                # Handle faq-specific parameters
                if block.definition_id == 'faq':
                    questions = params.get('questions', [])
                    if questions:
                        questions_toml = "["
                        for i, q in enumerate(questions):
                            if i > 0:
                                questions_toml += ", "
                            question = str(q.get("question", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            answer = str(q.get("answer", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            questions_toml += f'{{question = "{question}", answer = "{answer}"}}'
                        questions_toml += "]\n"
                        output += f'{indent}  questions = {questions_toml}'
                
                # Handle google_reviews-specific parameters
                if block.definition_id == 'google_reviews':
                    reviews = params.get('reviews', [])
                    if reviews:
                        reviews_toml = "["
                        for i, r in enumerate(reviews):
                            if i > 0:
                                reviews_toml += ", "
                            name = str(r.get("name", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            rating = str(r.get("rating", "5")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            text = str(r.get("text", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            date = str(r.get("date", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            image = str(r.get("image", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            reviews_toml += f'{{name = "{name}", rating = "{rating}", text = "{text}", date = "{date}", image = "{image}"}}'
                        reviews_toml += "]\n"
                        output += f'{indent}  reviews = {reviews_toml}'
                
                # Handle flip_cards-specific parameters
                if block.definition_id == 'flip_cards':
                    cards = params.get('cards', [])
                    if cards:
                        cards_toml = "["
                        for i, card in enumerate(cards):
                            if i > 0:
                                cards_toml += ", "
                            front_title = str(card.get("front_title", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            front_icon = str(card.get("front_icon", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            back_desc = str(card.get("back_description", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            back_cta_text = str(card.get("back_cta_text", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            back_cta_url = str(card.get("back_cta_url", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            cards_toml += f'{{front_title = "{front_title}", front_icon = "{front_icon}", back_description = "{back_desc}", back_cta_text = "{back_cta_text}", back_cta_url = "{back_cta_url}"}}'
                        cards_toml += "]\n"
                        output += f'{indent}  cards = {cards_toml}'
                
                # Handle accordion-specific parameters
                if block.definition_id == 'accordion':
                    items = params.get('items', [])
                    if items:
                        items_toml = "["
                        for i, item in enumerate(items):
                            if i > 0:
                                items_toml += ", "
                            title = str(item.get("title", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            content = str(item.get("content", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            items_toml += f'{{title = "{title}", content = "{content}"}}'
                        items_toml += "]\n"
                        output += f'{indent}  items = {items_toml}'
                
                # Legacy carousel handling removed to support generic child nesting
                # if block.definition_id == 'carousel': ...
                
                
                # --- Recursive Child Rendering ---
                # Check for children (nested blocks)
                children = BlockInstance.objects.filter(parent=block).order_by('sort_order')
                if children.exists():
                    # Render children into a 'blocks' array of the current block
                    # In TOML, [[parent.blocks]] appends to the 'blocks' array of the most recently defined 'parent'
                    output += render_blocks(children, f"{zone_name}.blocks", depth + 1)
                    
                    output += "\n"
            
            return output
        
            # Get layout definition
        try:
            layout_def = LayoutTemplate.objects.get(id=page.layout)
        except LayoutTemplate.DoesNotExist:
            # Fallback to standard layout if not found
            # Try 'single' or 'home' depending on page type, or just log warning
            try:
                layout_def = LayoutTemplate.objects.get(id='single')
            except LayoutTemplate.DoesNotExist:
                # Should not happen if seeded correctly, but handle gracefully
                layout_def = None

        # Render blocks from dynamic zones defined in layout
        if layout_def:
            for zone in layout_def.zones:
                zone_name = zone['name']
                scope = zone.get('scope', 'page')
                
                if scope == 'global':
                    zone_blocks = global_blocks.filter(placement_key=zone_name)
                else:
                    zone_blocks = page_blocks.filter(placement_key=zone_name)
                    
                if zone_blocks.exists():
                    content += render_blocks(zone_blocks, f'{zone_name}_blocks')
        else:
            # Fallback for legacy/undefined layouts
            for zone in ['header', 'main', 'sidebar', 'footer']:
                if zone in ['header', 'footer']:
                    zone_blocks = global_blocks.filter(placement_key=zone)
                else:
                    zone_blocks = page_blocks.filter(placement_key=zone)
                    
                if zone_blocks.exists():
                    content += render_blocks(zone_blocks, f'{zone}_blocks')
        
        # Close frontmatter
        return frontmatter + content + "+++\n"
    
    def _generate_site_config(self, website):
        """
        Generate hugo.toml configuration file.
        """
        title = website.name.replace('"', '\\"')
        
        config = f"""baseURL = "https://example.com/"
languageCode = "en-us"
title = "{title}"

[params]
  description = "A site built with Hugo CMS"
"""
        return config
class StorageSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = StorageSettingsSerializer
    
    def get_queryset(self):
        queryset = StorageSettings.objects.all()
        website_id = self.request.query_params.get('website_id')
        if website_id:
            queryset = queryset.filter(website_id=website_id)
        return queryset
    
    def perform_create(self, serializer):
        website_id = self.request.data.get('website_id')
        website = Website.objects.get(id=website_id)
        serializer.save(website=website)

class FileUploadViewSet(viewsets.ViewSet):
    
    def list(self, request):
        website_id = request.query_params.get('website_id')
        if not website_id:
            return Response({'error': 'website_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        files = UploadedFile.objects.filter(website_id=website_id).order_by('-uploaded_at')
        serializer = UploadedFileSerializer(files, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        file_obj = request.FILES.get('file')
        website_id = request.data.get('website_id')
        
        if not file_obj or not website_id:
            return Response({'error': 'File and website_id are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            website = Website.objects.get(id=website_id)
            settings, _ = StorageSettings.objects.get_or_create(website=website)
            
            # Generate unique filename
            ext = file_obj.name.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            
            if settings.storage_type == 's3':
                import boto3
                from botocore.exceptions import ClientError
                
                s3 = boto3.client(
                    's3',
                    endpoint_url=settings.s3_endpoint,
                    aws_access_key_id=settings.s3_access_key,
                    aws_secret_access_key=settings.s3_secret_key,
                    region_name=settings.s3_region
                )
                
                path = f"{website.slug}/{filename}"
                s3.upload_fileobj(
                    file_obj, 
                    settings.s3_bucket, 
                    path,
                    ExtraArgs={'ACL': 'public-read', 'ContentType': file_obj.content_type}
                )
                
                # Construct public URL
                if settings.s3_public_url:
                    file_url = f"{settings.s3_public_url.rstrip('/')}/{path}"
                else:
                    # Fallback to endpoint/bucket style if no public URL configured
                    file_url = f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/{path}"
                    
            else:
                # Local Storage
                import os
                from django.conf import settings as django_settings
                
                # Create directory structure: media/uploads/{website_slug}/
                upload_dir = os.path.join(django_settings.MEDIA_ROOT, 'uploads', website.slug)
                os.makedirs(upload_dir, exist_ok=True)
                
                path = os.path.join('uploads', website.slug, filename)
                full_path = os.path.join(django_settings.MEDIA_ROOT, path)
                
                with open(full_path, 'wb+') as destination:
                    for chunk in file_obj.chunks():
                        destination.write(chunk)
                        
                file_url = f"{django_settings.MEDIA_URL}{path}"
            
            # Save record
            uploaded_file = UploadedFile.objects.create(
                website=website,
                filename=file_obj.name,
                file_path=path,
                file_url=file_url,
                file_size=file_obj.size,
                content_type=file_obj.content_type
            )
            
            return Response(UploadedFileSerializer(uploaded_file).data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                print(f"DEBUG: Processing Block ID {block['id']} (Definition: {block['type']})")
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
                children_data = block_data['children']
                
                # Check if children are in column format (flex_columns style: [{blocks: [...]}])
                # or direct format (row/column style: [{id, type, params}...])
                is_column_format = len(children_data) > 0 and isinstance(children_data[0], dict) and 'blocks' in children_data[0]
                
                if is_column_format:
                    # Column format: children = [{blocks: [...]}, {blocks: [...]}]
                    # Delete old children of this parent not present in the incoming payload
                    incoming_child_ids = []
                    for col in children_data:
                         if col.get('blocks'):
                             for child in col['blocks']:
                                 if 'id' in child: incoming_child_ids.append(child['id'])
                    
                    block_instance.children.exclude(id__in=incoming_child_ids).delete()

                    for col_index, col_data in enumerate(children_data):
                        if col_data.get('blocks'):
                            col_placement_key = f"col_{col_index}"
                            self._save_blocks_recursive(
                                col_data['blocks'], 
                                placement_key=col_placement_key, 
                                page=None,
                                parent=block_instance,
                                website=website
                            )
                else:
                    # Direct format: children = [{id, type, params}, ...]
                    # Delete old children not in the incoming payload
                    incoming_child_ids = [child.get('id') for child in children_data if child.get('id')]
                    block_instance.children.exclude(id__in=incoming_child_ids).delete()
                    
                    # Recursively save the children directly
                    self._save_blocks_recursive(
                        children_data, 
                        placement_key='children', 
                        page=None,
                        parent=block_instance,
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
    
    def perform_create(self, serializer):
        """
        Ensure that newly created pages have a website assigned.
        The frontend should pass the website field.
        """
        if not serializer.validated_data.get('website'):
            raise serializers.ValidationError({
                'website': 'Website is required when creating a page'
            })
        serializer.save()

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
                children_data = block_data['children']
                
                # Check if children are in column format (flex_columns style: [{blocks: [...]}])
                # or direct format (row/column style: [{id, type, params}...])
                is_column_format = len(children_data) > 0 and isinstance(children_data[0], dict) and 'blocks' in children_data[0]
                
                if is_column_format:
                    # Column format: children = [{blocks: [...]}, {blocks: [...]}]
                    incoming_child_ids = []
                    for col in children_data:
                         if col.get('blocks'):
                             for child in col['blocks']:
                                 if 'id' in child: incoming_child_ids.append(child['id'])
                    
                    block_instance.children.exclude(id__in=incoming_child_ids).delete()

                    for col_index, col_data in enumerate(children_data):
                        if col_data.get('blocks'):
                            col_placement_key = f"col_{col_index}"
                            self._save_blocks_recursive(
                                col_data['blocks'], 
                                placement_key=col_placement_key, 
                                page=None, 
                                parent=block_instance
                            )
                else:
                    # Direct format: children = [{id, type, params}, ...]
                    incoming_child_ids = [child.get('id') for child in children_data if child.get('id')]
                    block_instance.children.exclude(id__in=incoming_child_ids).delete()
                    
                    self._save_blocks_recursive(
                        children_data, 
                        placement_key='children', 
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
    

class DeploymentProviderViewSet(viewsets.ModelViewSet):
    queryset = DeploymentProvider.objects.all()
    serializer_class = DeploymentProviderSerializer


# --- Template Viewsets ---

from .models import SiteTemplate, TemplateCategory
from .serializers import (
    TemplateCategorySerializer,
    SiteTemplateListSerializer,
    SiteTemplateDetailSerializer,
    CreateTemplateFromWebsiteSerializer,
    CreateWebsiteFromTemplateSerializer
)
from .template_service import export_website_to_template, create_website_from_template


class TemplateCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve template categories.
    """
    queryset = TemplateCategory.objects.all()
    serializer_class = TemplateCategorySerializer


class SiteTemplateViewSet(viewsets.ModelViewSet):
    """
    List, retrieve, create, update, and delete site templates.
    Also provides actions to export a website to a template and create a website from a template.
    """
    queryset = SiteTemplate.objects.filter(is_public=True)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SiteTemplateListSerializer
        return SiteTemplateDetailSerializer
    
    @action(detail=False, methods=['post'])
    def from_website(self, request):
        """
        Export a website to create a new template.
        
        POST /api/templates/from-website/
        {
            "website_id": "uuid",
            "template_id": "therapy",
            "name": "Therapy Practice",
            "description": "A template for therapy websites",
            "category": "healthcare",
            "thumbnail_url": "https://..."
        }
        """
        serializer = CreateTemplateFromWebsiteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            template = export_website_to_template(
                website_id=serializer.validated_data['website_id'],
                template_id=serializer.validated_data['template_id'],
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                category_slug=serializer.validated_data.get('category'),
                thumbnail_url=serializer.validated_data.get('thumbnail_url', ''),
                created_by=request.user.username if request.user.is_authenticated else ''
            )
            
            return Response({
                'success': True,
                'message': f'Template "{template.name}" created successfully',
                'template': SiteTemplateDetailSerializer(template).data
            }, status=status.HTTP_201_CREATED)
            
        except Website.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Website not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def create_website(self, request, pk=None):
        """
        Create a new website from this template.
        
        POST /api/templates/{id}/create-website/
        {
            "website_name": "My Therapy Site",
            "website_slug": "my-therapy-site"
        }
        """
        try:
            template = self.get_object()
            
            website_name = request.data.get('website_name')
            website_slug = request.data.get('website_slug')
            
            if not website_name or not website_slug:
                return Response({
                    'success': False,
                    'error': 'website_name and website_slug are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if slug already exists
            if Website.objects.filter(slug=website_slug).exists():
                return Response({
                    'success': False,
                    'error': f'Website with slug "{website_slug}" already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            website = create_website_from_template(
                template_id=template.id,
                website_name=website_name,
                website_slug=website_slug
            )
            
            return Response({
                'success': True,
                'message': f'Website "{website.name}" created from template "{template.name}"',
                'website': WebsiteSerializer(website).data
            }, status=status.HTTP_201_CREATED)
            
        except SiteTemplate.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Template not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
