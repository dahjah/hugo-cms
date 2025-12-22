
from django.core.management.base import BaseCommand
from django.conf import settings
from hugo.models import Website, Page, BlockInstance
from pathlib import Path
import shutil
import os
import json
import uuid
from hugo.management.commands.compile_templates import TemplateCompiler


class Command(BaseCommand):
    help = 'Generate Hugo site files (Restored Logic + Media Fix)'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Website slug')
        parser.add_argument('--keep-existing', action='store_true', help='Skip cleaning the output directory and use incremental build')
        parser.add_argument('--page-id', type=str, help='Specific Page ID to publish (incremental)')

    def handle(self, *args, **options):
        slug = options['slug']
        keep_existing = options.get('keep_existing')
        page_id = options.get('page_id')

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
        
        # Clean (Unless incremental)
        if not keep_existing:
             if output_dir.exists():
                 shutil.rmtree(output_dir)
             output_dir.mkdir(parents=True, exist_ok=True)
             content_dir.mkdir(parents=True, exist_ok=True)
             static_dir.mkdir(parents=True, exist_ok=True)
        else:
             # Ensure they exist anyway
             output_dir.mkdir(parents=True, exist_ok=True)
             content_dir.mkdir(parents=True, exist_ok=True)
             static_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate Site Config (hugo.toml)
        self.generate_config(output_dir, website)

        # 2. Generate Layouts (Templates)
        self.generate_layouts(output_dir, website)
        self.generate_fixed_templates(output_dir)

        # 3. Generate Pages
        self.generate_pages_original(website, content_dir, page_id=page_id)
        
        # 4. Copy Media (Incremental-aware)
        self.copy_media(website, static_dir, incremental=keep_existing)
        
        # 5. Run Hugo build to generate hugo_stats.json
        self.run_hugo_build(output_dir)
        
        # 6. Compile and Copy Tailwind CSS (reads hugo_stats.json)
        self.compile_css(static_dir, website)
        
        self.stdout.write(self.style.SUCCESS(f"Site generated in {output_dir}"))

    # ... generate_config, generate_layouts ...

    def generate_pages_original(self, website, content_dir, page_id=None):
        import json
        from django.utils import timezone
        now = timezone.now()
        
        pages = website.pages.all()
        if page_id:
            pages = pages.filter(id=page_id)
        
        for page in pages:
            page_data = self._build_page_dict(page)
            
            # Serialize to JSON (valid YAML) wrapped in ---
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
            'draft': page.status != 'published'
        }
        
        if page.description:
            data['description'] = page.description
            
        is_homepage = (page.slug == '/' or page.slug == '')
        if is_homepage:
            data['type'] = page.layout
        else:
            data['layout'] = page.layout

    # ... other methods ...

    def copy_media(self, website, static_dir, incremental=False):
        media_root = Path(settings.MEDIA_ROOT)
        static_media = static_dir / 'media'
        static_media.mkdir(parents=True, exist_ok=True)
        
        count = 0
        skipped = 0
        for uf in website.files.all():
             src = media_root / uf.file_path
             if src.exists():
                 dest = static_media / uf.file_path
                 dest.parent.mkdir(parents=True, exist_ok=True)
                 
                 should_copy = True
                 if incremental and dest.exists():
                     # Only copy if source is newer or different size
                     if src.stat().st_mtime <= dest.stat().st_mtime and src.stat().st_size == dest.stat().st_size:
                         should_copy = False
                 
                 if should_copy:
                     shutil.copy2(src, dest)
                     count += 1
                 else:
                     skipped += 1
                     
        msg = f"Copied {count} media files."
        if incremental:
            msg += f" (Skipped {skipped} unchanged)"
        self.stdout.write(msg)

    def generate_config(self, output_dir, website):
        # Basic config generation
        print(f"DEBUG: Generating config for {website.slug}. Theme: {getattr(website, 'theme_preset', 'None')}")
        with open(output_dir / 'hugo.toml', 'w') as f:
            f.write(f"""
baseURL = 'https://{website.slug}.monu.dev'
languageCode = 'en-us'
title = '{website.name}'
theme = []

[params]
    description = '{getattr(website, "description", "")}'
    theme_preset = '{getattr(website, "theme_preset", "default")}'
    
[build]
    writeStats = true

[[build.cachebusters]]
    source = "hugo_stats.json"
    target = "styles.css"
    
[mediaTypes]
[mediaTypes."text/css"]
    suffixes = ["css"]
            """)

    def generate_layouts(self, output_dir, website):
        # Basic layout generation
        layouts = output_dir / 'layouts'
        defaults = layouts / '_default'
        partials = layouts / 'partials'
        blocks = partials / 'blocks'
        
        for d in [layouts, defaults, partials, blocks]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Baseof
        print("DEBUG: Writing baseof.html with banner...")
        theme = website.theme_preset
        with open(defaults / 'baseof.html', 'w') as f:
            baseof = f"""<!DOCTYPE html>
<html lang="{{{{ .Site.LanguageCode }}}}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ .Title }}}} | {{{{ .Site.Title }}}}</title>
    <link rel="stylesheet" href="/css/styles.css">
    <link rel="stylesheet" href="/css/custom.css">
</head>
<body class="bg-base-200 text-base-content font-sans min-h-screen flex flex-col" data-theme="{{{{ .Site.Params.theme_preset }}}}">
    <div id="debug-info" data-theme="{theme}" style="background: #333; color: #fff; padding: 10px; font-family: monospace; z-index: 9999; position: relative; display: none;">
        <strong>DEBUG INFO:</strong> <span class="badge badge-primary">Theme: {theme}</span><br>
        Theme Preset: [{{{{ site.Params.theme_preset }}}}]<br>
    </div>
    <script>
        if (new URLSearchParams(window.location.search).get('debug') === 'true') {{
            document.getElementById('debug-info').style.display = 'block';
        }}
    </script>
    {{{{ block "main" . }}}}{{{{ end }}}}
</body>
</html>"""
            f.write(baseof)
        
        # Single/List
        single = """{{ define "main" }}
<div class="flex flex-col min-h-screen">
    {{ if .Params.header_blocks }}
    <header style="display: contents">
        {{ range .Params.header_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </header>
    {{ end }}
    <main class="flex-1 w-full">
        {{ range .Params.main_blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </main>
    <footer class="w-full mt-auto border-t bg-base-300 border-base-300 text-base-content">
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
        
        with open(blocks / 'render-block.html', 'w') as f:
             f.write("""{{ if .block_type }}
    {{ $partialPath := printf "blocks/%s.html" .block_type }}
    {{ if templates.Exists (printf "partials/%s" $partialPath) }}
        <div class="cms-block-wrapper" data-block-id="{{ .id }}" style="display: contents;">
            {{ partial $partialPath . }}
        </div>
    {{ else }}
        <div class="p-4 border border-red-200 bg-red-50 text-red-700 rounded my-4">
            <strong>Missing Block Template:</strong> {{ .block_type }}
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
        {{ range .items }}
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
    <h2 class="text-3xl font-bold text-center mb-10 text-base-content">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {{ range .items }}
        <div class="group rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border border-base-300 flex flex-col h-full">
            {{ if .image }}
            <div class="relative h-48 overflow-hidden bg-base-200">
                <img src="{{ .image }}?v=2" alt="{{ .name }}" 
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                     onerror="this.onerror=null;this.parentElement.style.display='none';"/>
            </div>
            {{ end }}
            <div class="p-5 flex-1 flex flex-col">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="text-lg font-bold text-base-content leading-tight">{{ .name }}</h4>
                </div>
                {{ if .description }}
                <p class="text-sm opacity-70 leading-snug flex-1">{{ .description }}</p>
                {{ end }}
                <div class="mt-4 pt-4 border-t border-base-300 flex items-center justify-between text-xs font-medium opacity-60 uppercase tracking-wider">
                     <span>Menu Item</span>
                     <span class="text-primary">Order Now</span>
                </div>
            </div>
        </div>
        {{ end }}
    </div>
</div>"""
        
        # --- DAISY UI VARIANTS ---
        daisy_features = """
<div class="py-16 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-12 text-base-content">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {{ range .items }}
        <div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300">
            <div class="card-body items-center text-center">
                {{ if .icon }}
                <div class="w-16 h-16 mb-4 text-primary">
                    {{ if eq .icon "truck" }}<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0"></path></svg>
                    {{ else }}<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                    {{ end }}
                </div>
                {{ end }}
                <h2 class="card-title">{{ .title }}</h2>
                <p>{{ .description }}</p>
            </div>
        </div>
        {{ end }}
    </div>
</div>"""

        daisy_menu = """
<div class="py-12 px-4 {{ .css_classes }}">
    {{ if .title }}
    <h2 class="text-3xl font-bold text-center mb-10 text-base-content">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {{ range .items }}
        <div class="card card-compact shadow-xl hover:shadow-2xl transition-all duration-300">
            {{ if .image }}
            <figure class="h-48 overflow-hidden">
                <img src="{{ .image }}?v=2" alt="{{ .name }}" 
                     class="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                     onerror="this.onerror=null;this.parentElement.style.display='none';"/>
            </figure>
            {{ end }}
            <div class="card-body">
                <h2 class="card-title text-base-content">{{ .name }}</h2>
                {{ if .description }}
                <p class="text-base-content/70">{{ .description }}</p>
                {{ end }}
                <div class="card-actions justify-end mt-4">
                    <button class="btn btn-primary btn-sm">Order Now</button>
                </div>
            </div>
        </div>
        {{ end }}
    </div>
</div>"""

        # Create directories
        themes_dir = output_dir / 'layouts' / 'partials' / 'themes'
        default_theme_dir = themes_dir / 'default'
        daisy_theme_dir = themes_dir / 'daisy'
        
        for d in [themes_dir, default_theme_dir, daisy_theme_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Write Dispatchers to main blocks folder
        blocks = output_dir / 'layouts' / 'partials' / 'blocks'
        
        # --- DISPATCHERS ---
        features_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/features_grid.html" $templateDir) . }}"""

        menu_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/menu_grid.html" $templateDir) . }}"""

        with open(blocks / 'features_grid.html', 'w') as f: f.write(features_dispatcher)
        with open(blocks / 'menu_grid.html', 'w') as f: f.write(menu_dispatcher)
        
        # Write Default Theme Files
        with open(default_theme_dir / 'features_grid.html', 'w') as f: f.write(fixed_features)
        with open(default_theme_dir / 'menu_grid.html', 'w') as f: f.write(fixed_menu)
        
        # Write Daisy Theme Files
        with open(daisy_theme_dir / 'features_grid.html', 'w') as f: f.write(daisy_features)
        with open(daisy_theme_dir / 'menu_grid.html', 'w') as f: f.write(daisy_menu)
        
        # --- STRUCTURAL BLOCKS ---
        section_tpl = """<div class="section py-12 {{ .css_classes }}" style="width:{{ .width | default "100%" }};margin:0 auto">
    <div class="container mx-auto px-4">
        {{ range .blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </div>
</div>"""

        row_tpl = """<div class="flex flex-wrap md:flex-nowrap justify-{{ .justify | default "start" }} items-{{ .align | default "stretch" }} gap-{{ .gap | default "4" }} {{ .css_classes | default .class }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>"""

        column_tpl = """<div class="{{ if .width_percent }}w-full md:w-[{{ .width_percent }}%]{{ else }}flex-initial w-full md:w-auto{{ end }} {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>"""

        with open(blocks / 'section.html', 'w') as f: f.write(section_tpl)
        with open(blocks / 'row.html', 'w') as f: f.write(row_tpl)
        with open(blocks / 'column.html', 'w') as f: f.write(column_tpl)
        
        # Navbar (DaisyUI styled row)
        navbar_tpl = """<div class="flex flex-wrap md:flex-nowrap navbar bg-base-100/{{ .opacity | default 100 }} {{ if eq .position \"sticky\" }}sticky top-0 z-50 {{ end }}{{ if eq .position \"overlayed\" }}absolute top-0 left-0 right-0 z-50 {{ end }}justify-{{ .justify | default \"between\" }} items-{{ .align | default \"center\" }} gap-{{ .gap | default \"0\" }} {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>"""
        with open(blocks / 'navbar.html', 'w') as f: f.write(navbar_tpl)
        
        # --- CONTENT BLOCKS ---
        hero_tpl = """{{ $heroId := .id | default now.UnixNano }}
<div class="relative overflow-hidden w-full {{ .css_classes }} hero-section" 
     id="hero-{{ $heroId }}"
     data-parallax="{{ .parallax }}" 
     data-parallax-strength="{{ .parallax_strength | default 5 }}">
    <img src="{{ .bgImage | default .bg_image }}" alt="{{ .title }}" class="w-full h-64 md:h-96 object-cover will-change-transform" style="transform: scale(1.3);" loading="eager">
    <div class="absolute inset-0 bg-black/40 flex flex-col items-center justify-center text-center px-4">
        <div class="container mx-auto">
            <h1 class="text-3xl md:text-5xl font-bold text-white mb-4 drop-shadow-lg">{{ .title }}</h1>
            <p class="text-lg md:text-xl text-white/90 max-w-2xl mx-auto drop-shadow">{{ .subtitle }}</p>
            {{ if .cta_url }}
            <a href="{{ .cta_url }}" class="btn btn-primary btn-lg mt-6 rounded-full shadow-lg transition-all hover:scale-105">{{ .cta_text }}</a>
            {{ end }}
        </div>
    </div>
    {{ if .parallax }}
    <script>
    (function() {
        const hero = document.getElementById('hero-{{ $heroId }}');
        if (!hero) return;
        
        const img = hero.querySelector('img');
        const strength = parseInt(hero.dataset.parallaxStrength) || 5;
        
        function parallax() {
            const y = window.scrollY;
            // Use strength slider value in the multiplier (1-10 -> -0.025 to -0.25)
            // Negative = reverse scrolling (background moves opposite direction)
            img.style.transform = `scale(1.3) translateY(${-strength * 0.025 * y}px)`;
        }
        
        window.addEventListener('scroll', parallax, false);
    })();
    </script>
    {{ end }}
</div>"""

        markdown_tpl = """<div class="prose max-w-none py-6 {{ .css_classes }}">
    {{ .md | markdownify }}
</div>"""

        text_tpl = """<div class="prose max-w-none py-6 {{ .css_classes }}">
    {{ .content | markdownify }}
</div>"""

        button_tpl = """<div class="mb-4 {{ .css_classes }}">
    <a href="{{ .url }}" class="btn btn-{{ .style | default "primary" }} btn-lg rounded-lg shadow-md hover:shadow-lg">{{ .text }}</a>
</div>"""

        accordion_tpl = """<!-- Determine spacing based on .spacing parameter -->
{{ $gapClass := "gap-0" }}
{{ if eq .spacing "compact" }}{{ $gapClass = "gap-1" }}{{ end }}
{{ if eq .spacing "normal" }}{{ $gapClass = "gap-4" }}{{ end }}
{{ if eq .spacing "relaxed" }}{{ $gapClass = "gap-6" }}{{ end }}

<div class="join join-vertical w-full {{ $gapClass }} {{ .css_classes }}">
    {{ $id := .id }}
    {{ $allowMultiple := .allow_multiple }}
    {{ range $index, $item := .items }}
    <div tabindex="0" class="collapse collapse-arrow bg-base-100 join-item border border-base-300">
        <input type="{{ if $allowMultiple }}checkbox{{ else }}radio{{ end }}" name="accordion-{{ $id }}" id="accordion-{{ $id }}-{{ $index }}"{{ if $item._isOpen }} checked="checked"{{ end }} /> 
        <label for="accordion-{{ $id }}-{{ $index }}" class="collapse-title text-xl font-medium cursor-pointer">
            {{ $item.title }}
        </label>
        <div class="collapse-content"> 
            <div class="prose max-w-none">
                {{ $item.content | safeHTML }}
            </div>
        </div>
    </div>
    {{ end }}
</div>"""

        youtube_tpl = """<div class="w-full aspect-video rounded-lg overflow-hidden shadow-lg {{ .css_classes }}" style="width:{{ .width | default "100%" }};margin:0 auto">
    <iframe src="https://www.youtube.com/embed/{{ .videoId | default .params.videoId }}" class="w-full h-full" frameborder="0" allowfullscreen></iframe>
</div>"""

        alert_tpl = """<div role="alert" class="alert alert-{{ .type | default \"info\" }} {{ .css_classes }}">
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
  <span>{{ .message | safeHTML }}</span>
</div>"""

        testimonial_tpl = """<div class="card bg-base-100 shadow-xl border border-base-200 {{ .css_classes }}">
  <div class="card-body">
    <div class="flex items-center gap-4 mb-4">
        {{ if .avatar }}<div class="avatar"><div class="w-12 h-12 rounded-full"><img src="{{ .avatar }}" /></div></div>{{ end }}
        <div>
            <h2 class="card-title text-base">{{ .author }}</h2>
            <p class="text-sm opacity-70">{{ .role }}</p>
        </div>
    </div>
    <p class="italic text-base-content/80">"{{ .quote | default .text }}"</p>
  </div>
</div>"""

        html_tpl = """<div class="raw-html {{ .css_classes }}">
    {{ .content | safeHTML }}
</div>"""

        process_steps_tpl = """<ul class="steps {{ if eq .layout "vertical" }}steps-vertical{{ end }} w-full {{ .css_classes }}">
  {{ range .steps }}
  <li class="step step-primary" data-content="{{ if .icon }}✓{{ else }}●{{ end }}">
    <div class="text-left ml-2">
        <h3 class="font-bold">{{ .title }}</h3>
        <p class="text-sm opacity-70">{{ .description }}</p>
    </div>
  </li>
  {{ end }}
</ul>"""

        flip_cards_tpl = """<div class="grid grid-cols-1 md:grid-cols-{{ .columns | default 3 }} gap-6 {{ .css_classes }}">
    {{ range .cards }}
    <div class="card bg-base-100 shadow-xl group perspective-1000">
        <div class="relative w-full h-64 transition-all duration-500 preserve-3d group-hover:my-rotate-y-180" style="transform-style: preserve-3d;">
            <!-- Front -->
            <div class="absolute inset-0 backface-hidden flex flex-col items-center justify-center p-6 bg-base-100 border border-base-200 rounded-xl">
                {{ if .front_icon }}<div class="text-4xl mb-4 text-primary">{{ .front_icon }}</div>{{ end }}
                <h3 class="card-title text-center">{{ .front_title }}</h3>
            </div>
            <!-- Back -->
            <div class="absolute inset-0 backface-hidden my-rotate-y-180 flex flex-col items-center justify-center p-6 bg-primary text-primary-content rounded-xl" style="transform: rotateY(180deg);">
                <p class="text-center mb-4">{{ .back_description }}</p>
                {{ if .back_cta_text }}
                <a href="{{ .back_cta_url }}" class="btn btn-sm btn-outline btn-white bg-base-100 text-base-content hover:bg-base-200 border-none">{{ .back_cta_text }}</a>
                {{ end }}
            </div>
        </div>
    </div>
    {{ end }}
</div>
<style>
.perspective-1000 { perspective: 1000px; }
.preserve-3d { transform-style: preserve-3d; }
.backface-hidden { backface-visibility: hidden; -webkit-backface-visibility: hidden; }
.my-rotate-y-180 { transform: rotateY(180deg); }
</style>"""

        flex_columns_tpl = """{{ $widths := split (.col_widths | default "100") "," }}
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
</div>"""
        

        quote_tpl = """<blockquote class="border-l-4 border-primary pl-4 py-2 mb-8 italic text-base-content/80 {{ .css_classes }}">
    <p class="text-lg">"{{ .text }}"</p>
    {{ if .author }}<cite class="block mt-2 text-sm font-semibold text-base-content">- {{ .author }}</cite>{{ end }}
</blockquote>"""

        image_tpl = """<figure class="mb-8 {{ .css_classes }}" style="width:{{ .width | default "100%" }};margin:0 auto">
    <img src="{{ .src | default .params.src }}" alt="{{ .alt | default .params.alt }}" class="w-full rounded-lg shadow-md" style="height: auto; object-fit: cover;">
    {{ if or .caption .params.caption }}<figcaption class="text-center text-sm text-slate-500 mt-2">{{ .caption | default .params.caption }}</figcaption>{{ end }}
</figure>"""

        carousel_tpl = """{{ $carouselId := now.UnixNano }}
<div class="carousel-container py-8 {{ .css_classes }}" 
     data-carousel-id="{{ $carouselId }}"
     data-auto-advance="{{ .auto_advance | default true }}"
     data-interval="{{ .interval_seconds | default 5 }}">
    {{ if .slides }}
    <div class="relative" style="display: grid; grid-template-areas: 'stack'; place-items: center; min-height: 300px; overflow: hidden;">
        {{ range $index, $slide := .slides }}
        <div class="carousel-slide" data-slide-index="{{ $index }}" style="grid-area: stack; width: 85%; max-width: 900px; transition: transform 0.5s ease-in-out, opacity 0.5s ease-in-out; transform: translateX({{ if eq $index 0 }}0{{ else }}100%{{ end }}); opacity: {{ if eq $index 0 }}1{{ else }}0{{ end }}; pointer-events: {{ if eq $index 0 }}auto{{ else }}none{{ end }};">
            <div class="bg-base-100 rounded-lg shadow-md p-6">
                {{ range $slide.children }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            </div>
        </div>
        {{ end }}
        
        {{ if gt (len .slides) 1 }}
        <button data-carousel-prev style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); z-index: 10;" class="w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all bg-base-100/80 hover:bg-base-200 border border-base-200 backdrop-blur text-base-content hover:text-primary">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
        </button>
        <button data-carousel-next style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); z-index: 10;" class="w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all bg-base-100/80 hover:bg-base-200 border border-base-200 backdrop-blur text-base-content hover:text-primary">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
        </button>
        {{ end }}
    </div>
    
    {{ if gt (len .slides) 1 }}
    <div class="flex justify-center gap-3 mt-6">
        {{ range $index, $slide := .slides }}
        <button data-carousel-dot="{{ $index }}" class="transition-all duration-300 h-3 rounded-full {{ if eq $index 0 }}w-8 bg-primary{{ else }}w-3 bg-base-300 hover:bg-primary/50{{ end }}"></button>
        {{ end }}
    </div>
    {{ end }}
    
<script>
(function() {
    const container = document.querySelector('[data-carousel-id="{{ $carouselId }}"]');
    if (!container) return;
    
    const slides = container.querySelectorAll('.carousel-slide');
    const dots = container.querySelectorAll('[data-carousel-dot]');
    const prevBtn = container.querySelector('[data-carousel-prev]');
    const nextBtn = container.querySelector('[data-carousel-next]');
    const autoAdvance = container.dataset.autoAdvance === 'true';
    const interval = parseInt(container.dataset.interval) || 5;
    
    if (slides.length <= 1) return;
    
    let currentIndex = 0;
    let autoTimer = null;
    
    function showSlide(index) {
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
                dot.classList.remove('w-3', 'bg-base-300', 'hover:bg-primary/50');
                dot.classList.add('w-8', 'bg-primary');
            } else {
                dot.classList.remove('w-8', 'bg-primary');
                dot.classList.add('w-3', 'bg-base-300', 'hover:bg-primary/50');
            }
        });
        
        currentIndex = index;
        resetTimer();
    }
    
    function nextSlide() {
        showSlide((currentIndex + 1) % slides.length);
    }
    
    function prevSlide() {
        showSlide((currentIndex - 1 + slides.length) % slides.length);
    }
    
    function resetTimer() {
        if (autoTimer) clearInterval(autoTimer);
        if (autoAdvance) {
            autoTimer = setInterval(nextSlide, interval * 1000);
        }
    }
    
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => showSlide(index));
    });
    
    container.addEventListener('mouseenter', () => {
        if (autoTimer) clearInterval(autoTimer);
    });
    
    container.addEventListener('mouseleave', resetTimer);
    
    resetTimer();
})();
</script>
    {{ end }}
</div>"""

        # with open(blocks / 'hero.html', 'w') as f: f.write(hero_tpl)
        with open(blocks / 'markdown.html', 'w') as f: f.write(markdown_tpl)
        with open(blocks / 'button.html', 'w') as f: f.write(button_tpl)
        with open(blocks / 'accordion.html', 'w') as f: f.write(accordion_tpl)
        with open(blocks / 'quote.html', 'w') as f: f.write(quote_tpl)
        with open(blocks / 'image.html', 'w') as f: f.write(image_tpl)
        with open(blocks / 'carousel.html', 'w') as f: f.write(carousel_tpl)
        with open(blocks / 'youtube.html', 'w') as f: f.write(youtube_tpl)
        with open(blocks / 'alert.html', 'w') as f: f.write(alert_tpl)
        with open(blocks / 'testimonial.html', 'w') as f: f.write(testimonial_tpl)
        with open(blocks / 'html.html', 'w') as f: f.write(html_tpl)
        with open(blocks / 'process_steps.html', 'w') as f: f.write(process_steps_tpl)
        with open(blocks / 'flip_cards.html', 'w') as f: f.write(flip_cards_tpl)
                

        gallery_tpl = """<div class="py-12 {{ .css_classes }}">
    {{ if .title }}<h2 class="text-3xl font-bold text-center mb-8 text-base-content">{{ .title }}</h2>{{ end }}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 container mx-auto px-4">
        {{ range .images }}
        <div class="relative group overflow-hidden rounded-lg aspect-square bg-base-300">
             <img src="{{ .src }}" alt="{{ .alt }}" class="object-cover w-full h-full transition-transform duration-300 group-hover:scale-110">
             {{ if .caption }}
             <div class="absolute bottom-0 left-0 right-0 bg-base-100/90 text-base-content p-2 text-sm transform translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                {{ .caption }}
             </div>
             {{ end }}
        </div>
        {{ end }}
    </div>
</div>"""

        stats_counter_tpl = """<div class="py-12 bg-base-300 {{ .css_classes }}">
    <div class="container mx-auto px-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {{ range .stats }}
            <div class="bg-base-100 rounded-lg shadow-md p-6 text-center border border-base-300">
                {{ if .icon }}
                <div class="text-primary text-4xl mb-2">
                   <span>★</span> 
                </div>
                {{ end }}
                <div class="text-sm font-medium opacity-60 uppercase tracking-wide mb-2">{{ .label }}</div>
                <div class="text-4xl font-bold text-primary mb-1">{{ .value }}</div>
                {{ if .description }}<div class="text-sm opacity-70">{{ .description }}</div>{{ end }}
            </div>
            {{ end }}
        </div>
    </div>
</div>"""

        google_reviews_tpl = """<div class="py-16 {{ .css_classes }} bg-base-200">
    <div class="container mx-auto px-4">
        {{ if .title }}<h2 class="text-3xl font-bold text-center mb-12 text-base-content">{{ .title }}</h2>{{ end }}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {{ range .reviews }}
            <div class="bg-base-100 rounded-lg shadow-lg p-6 border border-base-300">
                <div class="flex items-center gap-4 mb-4">
                    {{ if .image }}
                    <div class="flex-shrink-0">
                        <img src="{{ .image }}" alt="{{ .name }}" class="w-12 h-12 rounded-full ring-2 ring-primary ring-offset-2 ring-offset-base-100" />
                    </div>
                    {{ else }}
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 rounded-full bg-primary text-primary-content flex items-center justify-center text-xl font-bold">
                            {{ substr .name 0 1 }}
                        </div>
                    </div>
                    {{ end }}
                    <div class="flex-1 min-w-0">
                        <h3 class="font-semibold text-base-content truncate">{{ .name }}</h3>
                        <div class="flex gap-1 mt-1">
                            {{ $rating := int (.rating | default "5") }}
                            {{ range $i := seq 1 5 }}
                            {{ if le $i $rating }}
                            <svg class="w-4 h-4 fill-current text-warning" viewBox="0 0 20 20">
                                <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                            </svg>
                            {{ else }}
                            <svg class="w-4 h-4 fill-current opacity-30" viewBox="0 0 20 20">
                                <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                            </svg>
                            {{ end }}
                            {{ end }}
                        </div>
                    </div>
                </div>
                <p class="text-sm opacity-80 italic leading-relaxed mb-3">"{{ .text }}"</p>
                <div class="flex justify-end">
                    <span class="text-xs opacity-60">{{ .date }}</span>
                </div>
            </div>
            {{ end }}
        </div>
    </div>
</div>"""

        default_social_links = """<div class="flex flex-wrap justify-center gap-4 py-6 {{ .css_classes }}">
    {{ range .links }}
    <a href="{{ .url }}" target="_blank" rel="noopener noreferrer" 
       class="w-12 h-12 rounded-full bg-slate-100 hover:bg-indigo-600 hover:text-white flex items-center justify-center text-slate-600 transition-all duration-200 shadow-sm hover:shadow-md">
        {{ if or (in .platform "instagram") (eq .platform "ig") }}
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M12.315 2c2.43 0 2.784.013 3.808.06 1.064.049 1.791.218 2.427.465a4.902 4.902 0 011.772 1.153 4.902 4.902 0 011.153 1.772c.247.636.416 1.363.465 2.427.048 1.067.06 1.407.06 4.123v.08c0 2.643-.012 2.987-.06 4.043-.049 1.064-.218 1.791-.465 2.427a4.902 4.902 0 01-1.153 1.772 4.902 4.902 0 01-1.772 1.153c-.636.247-1.363.416-2.427.465-1.067.048-1.407.06-4.123.06h-.08c-2.643 0-2.987-.012-4.043-.06-1.064-.049-1.791-.218-2.427-.465a4.902 4.902 0 01-1.772-1.153 4.902 4.902 0 01-1.153-1.772c-.247-.636-.416-1.363-.465-2.427-.047-1.024-.06-1.379-.06-3.808v-.63c0-2.43.013-2.784.06-3.808.049-1.064.218-1.791.465-2.427a4.902 4.902 0 011.153-1.772A4.902 4.902 0 015.468 2.373c.636-.247 1.363-.416 2.427-.465C8.901 2.013 9.256 2 11.685 2h.63zm-.081 1.802h-.468c-2.456 0-2.784.011-3.807.058-.975.045-1.504.207-1.857.344-.467.182-.8.398-1.15.748-.35.35-.566.683-.748 1.15-.137.353-.3.882-.344 1.857-.047 1.023-.058 1.351-.058 3.807v.468c0 2.456.011 2.784.058 3.807.045.975.207 1.504.344 1.857.182.466.399.8.748 1.15.35.35.683.566 1.15.748.353.137.882.3 1.857.344 1.054.048 1.37.058 4.041.058h.08c2.597 0 2.917-.01 3.96-.058.976-.045 1.505-.207 1.858-.344.466-.182.8-.398 1.15-.748.35-.35.566-.683.748-1.15.137-.353.3-.882.344-1.857.048-1.055.058-1.37.058-4.041v-.08c0-2.597-.01-2.917-.058-3.96-.045-.976-.207-1.505-.344-1.858a3.097 3.097 0 00-.748-1.15 3.098 3.098 0 00-1.15-.748c-.353-.137-.882-.3-1.857-.344-1.023-.047-1.351-.058-3.807-.058zM12 6.865a5.135 5.135 0 110 10.27 5.135 5.135 0 010-10.27zm0 1.802a3.333 3.333 0 100 6.666 3.333 3.333 0 000-6.666zm5.338-3.205a1.2 1.2 0 110 2.4 1.2 1.2 0 010-2.4z" clip-rule="evenodd" /></svg>
        {{ else if in .platform "facebook" }}
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clip-rule="evenodd" /></svg>
        {{ else if in .platform "twitter" }}
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>
        {{ else if in .platform "linkedin" }}
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clip-rule="evenodd" /></svg>
        {{ else }}
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
        {{ end }}
    </a>
    {{ end }}
</div>"""

        daisy_social_links = """<div class="flex flex-wrap justify-center gap-4 py-6 {{ .css_classes }}">
    {{ range .links }}
    <a href="{{ .url }}" target="_blank" rel="noopener noreferrer" 
       class="btn btn-circle btn-ghost hover:btn-primary text-2xl transition-all duration-300">
        {{ if or (in .platform "instagram") (eq .platform "ig") }}
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M12.315 2c2.43 0 2.784.013 3.808.06 1.064.049 1.791.218 2.427.465a4.902 4.902 0 011.772 1.153 4.902 4.902 0 011.153 1.772c.247.636.416 1.363.465 2.427.048 1.067.06 1.407.06 4.123v.08c0 2.643-.012 2.987-.06 4.043-.049 1.064-.218 1.791-.465 2.427a4.902 4.902 0 01-1.153 1.772 4.902 4.902 0 01-1.772 1.153c-.636.247-1.363.416-2.427.465-1.067.048-1.407.06-4.123.06h-.08c-2.643 0-2.987-.012-4.043-.06-1.064-.049-1.791-.218-2.427-.465a4.902 4.902 0 01-1.772-1.153 4.902 4.902 0 01-1.153-1.772c-.247-.636-.416-1.363-.465-2.427-.047-1.024-.06-1.379-.06-3.808v-.63c0-2.43.013-2.784.06-3.808.049-1.064.218-1.791.465-2.427a4.902 4.902 0 011.153-1.772A4.902 4.902 0 015.468 2.373c.636-.247 1.363-.416 2.427-.465C8.901 2.013 9.256 2 11.685 2h.63zm-.081 1.802h-.468c-2.456 0-2.784.011-3.807.058-.975.045-1.504.207-1.857.344-.467.182-.8.398-1.15.748-.35.35-.566.683-.748 1.15-.137.353-.3.882-.344 1.857-.047 1.023-.058 1.351-.058 3.807v.468c0 2.456.011 2.784.058 3.807.045.975.207 1.504.344 1.857.182.466.399.8.748 1.15.35.35.683.566 1.15.748.353.137.882.3 1.857.344 1.054.048 1.37.058 4.041.058h.08c2.597 0 2.917-.01 3.96-.058.976-.045 1.505-.207 1.858-.344.466-.182.8-.398 1.15-.748.35-.35.566-.683.748-1.15.137-.353.3-.882.344-1.857.048-1.055.058-1.37.058-4.041v-.08c0-2.597-.01-2.917-.058-3.96-.045-.976-.207-1.505-.344-1.858a3.097 3.097 0 00-.748-1.15 3.098 3.098 0 00-1.15-.748c-.353-.137-.882-.3-1.857-.344-1.023-.047-1.351-.058-3.807-.058zM12 6.865a5.135 5.135 0 110 10.27 5.135 5.135 0 010-10.27zm0 1.802a3.333 3.333 0 100 6.666 3.333 3.333 0 000-6.666zm5.338-3.205a1.2 1.2 0 110 2.4 1.2 1.2 0 010-2.4z" clip-rule="evenodd" /></svg>
        {{ else if in .platform "facebook" }}
        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clip-rule="evenodd" /></svg>
        {{ else if in .platform "twitter" }}
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>
        {{ else if in .platform "linkedin" }}
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clip-rule="evenodd" /></svg>
        {{ else }}
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
        {{ end }}
    </a>
    {{ end }}
</div>"""

        brand_logo_tpl = """<a href="{{ .link_url | default "/" }}" class="flex items-center gap-3 {{ .css_classes }} hover:opacity-80 transition-opacity no-underline">
    {{ if .logo_image }}
    <img src="{{ .logo_image }}" alt="{{ .brand_name }}" style="height: {{ .logo_size | default "40" }}px; width: auto;" class="object-contain">
    {{ end }}
    {{ if or .brand_name .tagline }}
    <div class="flex flex-col justify-center">
        {{ if .brand_name }}
        <span class="text-xl font-bold text-base-content leading-tight">{{ .brand_name }}</span>
        {{ end }}
        {{ if .tagline }}
        <span class="text-xs uppercase tracking-wider text-base-content/70 font-medium leading-tight">{{ .tagline }}</span>
        {{ end }}
    </div>
    {{ end }}
</a>"""

        # --- CREATE VANILLA TAILWIND VERSIONS FOR DEFAULT THEME ---
        
        default_google_reviews = """<div class="py-16 {{ .css_classes }} bg-slate-50">
    <div class="container mx-auto px-4">
        {{ if .title }}<h2 class="text-3xl font-bold text-center mb-12 text-slate-900">{{ .title }}</h2>{{ end }}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {{ range .reviews }}
            <div class="bg-white rounded-lg shadow-lg p-6 border border-slate-200">
                <div class="flex items-center gap-4 mb-4">
                    {{ if .image }}
                    <div class="flex-shrink-0">
                        <img src="{{ .image }}" alt="{{ .name }}" class="w-12 h-12 rounded-full ring-2 ring-indigo-500 ring-offset-2" />
                    </div>
                    {{ else }}
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xl font-bold">
                            {{ substr .name 0 1 }}
                        </div>
                    </div>
                    {{ end }}
                    <div class="flex-1 min-w-0">
                        <h3 class="font-semibold text-slate-900 truncate">{{ .name }}</h3>
                        <div class="flex gap-1 mt-1">
                            {{ $rating := int (.rating | default "5") }}
                            {{ range $i := seq 1 5 }}
                            {{ if le $i $rating }}
                            <svg class="w-4 h-4 fill-current text-orange-400" viewBox="0 0 20 20">
                                <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                            </svg>
                            {{ else }}
                            <svg class="w-4 h-4 fill-current text-slate-300" viewBox="0 0 20 20">
                                <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                            </svg>
                            {{ end }}
                            {{ end }}
                        </div>
                    </div>
                </div>
                <p class="text-sm text-slate-700 italic leading-relaxed mb-3">"{{ .text }}"</p>
                <div class="flex justify-end">
                    <span class="text-xs text-slate-500">{{ .date }}</span>
                </div>
            </div>
            {{ end }}
        </div>
    </div>
</div>"""

        default_accordion = """<div class="space-y-2 {{ .css_classes }}">
    {{ range .items }}
    <details class="group bg-white rounded-lg shadow-md overflow-hidden border border-slate-200">
        <summary class="cursor-pointer p-6 font-semibold text-slate-900 hover:bg-slate-50 transition-colors flex items-center justify-between list-none">
            <span>{{ .title }}</span>
            <svg class="w-5 h-5 text-slate-500 transform transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
        </summary>
        <div class="px-6 pb-6 text-slate-600 border-t border-slate-100 pt-4">
            {{ .content | markdownify }}
        </div>
    </details>
    {{ end }}
</div>"""

        default_stats = """<div class="py-12 bg-slate-100 {{ .css_classes }}">
    <div class="container mx-auto px-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {{ range .stats }}
            <div class="bg-white rounded-lg shadow-md p-6 text-center border border-slate-200">
                {{ if .icon }}
                <div class="text-indigo-600 text-4xl mb-2">
                   <span>★</span> 
                </div>
                {{ end }}
                <div class="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">{{ .label }}</div>
                <div class="text-4xl font-bold text-indigo-600 mb-1">{{ .value }}</div>
                {{ if .description }}<div class="text-sm text-slate-600">{{ .description }}</div>{{ end }}
            </div>
            {{ end }}
        </div>
    </div>
</div>"""

        default_gallery = """<div class="py-12 {{ .css_classes }}">
    {{ if .title }}<h2 class="text-3xl font-bold text-center mb-8 text-slate-900">{{ .title }}</h2>{{ end }}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 container mx-auto px-4">
        {{ range .images }}
        <div class="relative group overflow-hidden rounded-lg aspect-square bg-slate-200">
             <img src="{{ .src }}" alt="{{ .alt }}" class="object-cover w-full h-full transition-transform duration-300 group-hover:scale-110">
             {{ if .caption }}
             <div class="absolute bottom-0 left-0 right-0 bg-black/70 text-white p-2 text-sm transform translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                {{ .caption }}
             </div>
             {{ end }}
        </div>
        {{ end }}
    </div>
</div>"""

        # --- CREATE DISPATCHERS ---
        google_reviews_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/google_reviews.html" $templateDir) . }}"""

        accordion_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/accordion.html" $templateDir) . }}"""

        stats_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/stats_counter.html" $templateDir) . }}"""

        gallery_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/gallery.html" $templateDir) . }}"""

        social_links_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/social_links.html" $templateDir) . }}"""

        # Write dispatchers to blocks/
        with open(blocks / 'google_reviews.html', 'w') as f: f.write(google_reviews_dispatcher)
        with open(blocks / 'accordion.html', 'w') as f: f.write(accordion_dispatcher)
        with open(blocks / 'stats.html', 'w') as f: f.write(stats_dispatcher)
        with open(blocks / 'stats_counter.html', 'w') as f: f.write(stats_dispatcher)
        with open(blocks / 'gallery.html', 'w') as f: f.write(gallery_dispatcher)
        with open(blocks / 'social_links.html', 'w') as f: f.write(social_links_dispatcher)

        
        # Write default theme versions
        with open(default_theme_dir / 'google_reviews.html', 'w') as f: f.write(default_google_reviews)
        with open(default_theme_dir / 'accordion.html', 'w') as f: f.write(default_accordion)
        with open(default_theme_dir / 'stats_counter.html', 'w') as f: f.write(default_stats)
        with open(default_theme_dir / 'gallery.html', 'w') as f: f.write(default_gallery)
        with open(default_theme_dir / 'social_links.html', 'w') as f: f.write(default_social_links)
        
        # Write daisy theme versions (using existing DaisyUI templates)
        with open(daisy_theme_dir / 'google_reviews.html', 'w') as f: f.write(google_reviews_tpl)
        with open(daisy_theme_dir / 'accordion.html', 'w') as f: f.write(accordion_tpl)
        with open(daisy_theme_dir / 'stats_counter.html', 'w') as f: f.write(stats_counter_tpl)
        with open(daisy_theme_dir / 'gallery.html', 'w') as f: f.write(gallery_tpl)
        with open(daisy_theme_dir / 'social_links.html', 'w') as f: f.write(daisy_social_links)
        default_menu = """{{ $position := .position | default "normal" }}
{{ $isAlwaysHamburger := or (eq .responsive true) (eq .responsive "true") }}
{{ $hamburgerDir := .hamburgerDirection | default "dropdown" }}
{{ $alignment := .alignment | default "left" }}
{{ $justifyClass := "justify-start" }}
{{ if eq $alignment "center" }}
    {{ $justifyClass = "justify-center" }}
{{ else if eq $alignment "right" }}
    {{ $justifyClass = "justify-end" }}
{{ else if eq $alignment "between" }}
    {{ $justifyClass = "justify-between" }}
{{ end }}
{{ $classes := "bg-white shadow-sm border-b border-slate-200 mb-8" }}
{{ if eq $position "overlay" }}
    {{ $classes = "absolute top-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-sm shadow-md" }}
{{ else if eq $position "fixed" }}
    {{ $classes = "fixed top-0 left-0 right-0 z-40 bg-white shadow-md" }}
{{ end }}

<nav class="{{ $classes }} {{ .css_classes }}">
    <div class="container mx-auto px-4">
        <div class="flex items-center {{ $justifyClass }} h-16">
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
</div>
{{ end }}

<script>
    // Menu Toggle Logic
    const dropdownToggle = document.getElementById('dropdown-menu-toggle');
    const dropdownMenu = document.getElementById('dropdown-menu');
    const sidebarToggle = document.getElementById('sidebar-menu-toggle');
    const sidebarPanel = document.getElementById('sidebar-panel');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const sidebarClose = document.getElementById('sidebar-close');

    if (dropdownToggle && dropdownMenu) {
        dropdownToggle.addEventListener('click', () => {
            dropdownMenu.classList.toggle('hidden');
        });
    }

    if (sidebarToggle && sidebarPanel && sidebarOverlay && sidebarClose) {
        function openSidebar() {
            sidebarPanel.classList.remove('translate-x-full', '-translate-x-full');
            sidebarOverlay.classList.remove('hidden');
            setTimeout(() => sidebarOverlay.classList.remove('opacity-0'), 10); 
        }

        function closeSidebar() {
            const side = '{{ .sidebarSide }}' || 'left';
            sidebarPanel.classList.add(side === 'right' ? 'translate-x-full' : '-translate-x-full');
            sidebarOverlay.classList.add('opacity-0');
            setTimeout(() => sidebarOverlay.classList.add('hidden'), 300);
        }

        sidebarToggle.addEventListener('click', openSidebar);
        sidebarClose.addEventListener('click', closeSidebar);
        sidebarOverlay.addEventListener('click', closeSidebar);
    }
</script>"""

        daisy_menu = """{{ $position := .position | default "normal" }}
{{ $isAlwaysHamburger := or (eq .responsive true) (eq .responsive "true") }}
{{ $hamburgerDir := .hamburgerDirection | default "dropdown" }}
{{ $alignment := .alignment | default "left" }}
{{ $side := .sidebarSide | default "left" }}
{{ $navbarStartClass := "" }}
{{ $navbarCenterClass := "" }}
{{ $navbarEndClass := "" }}

{{ if eq $alignment "center" }}
    {{ $navbarCenterClass = "flex-1" }}
    {{ $navbarStartClass = "flex-1" }} 
    {{ $navbarEndClass = "flex-1 justify-end" }}
{{ else if eq $alignment "right" }}
    {{ $navbarStartClass = "flex-1" }}
    {{ $navbarEndClass = "flex-none" }}
{{ else }}
    {{ $navbarStartClass = "flex-1" }}
    {{ $navbarEndClass = "flex-none" }}
{{ end }}

{{ $classes := "navbar shadow-sm z-40 w-auto" }}
{{ if eq $position "overlay" }}
    {{ $classes = "navbar absolute top-0 left-0 right-0 z-40 bg-base-100/90 backdrop-blur-sm shadow-md w-full" }}
{{ else if eq $position "fixed" }}
    {{ $classes = "navbar fixed top-0 left-0 right-0 z-40 shadow-md w-full" }}
{{ end }}

<div class="{{ $classes }} {{ .css_classes }}">
    <!-- Navbar Start (Logo or Hamburger for sidebar) -->
    <div class="navbar-start">
        {{ if eq $hamburgerDir "sidebar" }}
        <div class="{{ if not $isAlwaysHamburger }}lg:hidden{{ end }}">
            <label class="btn btn-ghost btn-circle swap swap-rotate">
                <!-- this hidden checkbox controls the state -->
                <input type="checkbox" id="daisy-sidebar-checkbox" class="hidden" style="display:none;" />
                
                <!-- hamburger icon -->
                <svg class="swap-off fill-current" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 512 512"><path d="M64,384H448V341.33H64Zm0-106.67H448V234.67H64ZM64,128v42.67H448V128Z"/></svg>
                
                <!-- close icon -->
                <svg class="swap-on fill-current" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 512 512"><polygon points="400 145.49 366.51 112 256 222.51 145.49 112 112 145.49 222.51 256 112 366.51 145.49 400 256 289.49 366.51 400 400 366.51 289.49 256 400 145.49"/></svg>
            </label>
        </div>
        {{ else if eq $hamburgerDir "dropdown" }}
        <div class="dropdown {{ if not $isAlwaysHamburger }}lg:hidden{{ end }}">
            <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" /></svg>
            </div>
            <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[50] p-2 shadow bg-base-100 rounded-box w-52">
                {{ range .items }}
                <li><a href="{{ .url }}">{{ .label }}</a></li>
                {{ end }}
            </ul>
        </div>
        {{ end }}
    </div>

    <!-- Navbar Center (Hidden on mobile usually, or main links) -->
    <div class="navbar-center {{ if not $isAlwaysHamburger }}hidden lg:flex{{ else }}hidden{{ end }}">
        {{ if eq $alignment "center" }}
        <ul class="menu menu-horizontal px-1">
            {{ range .items }}
            <li><a href="{{ .url }}">{{ .label }}</a></li>
            {{ end }}
        </ul>
        {{ end }}
    </div>

    <!-- Navbar End (Links if right aligned, or buttons) -->
    <div class="navbar-end">
        {{ if ne $alignment "center" }}
        <ul class="menu menu-horizontal px-1 {{ if not $isAlwaysHamburger }}hidden lg:flex{{ else }}hidden{{ end }}">
            {{ range .items }}
            <li><a href="{{ .url }}">{{ .label }}</a></li>
            {{ end }}
        </ul>
        {{ end }}
    </div>
</div>

{{ if eq $hamburgerDir "sidebar" }}
<!-- Sidebar Overlay and Panel (Drawer Style) -->
{{ $sideClass := "left-0" }}
{{ $transClass := "-translate-x-full" }}
{{ if eq $side "right" }}
    {{ $sideClass = "right-0" }}
    {{ $transClass = "translate-x-full" }}
{{ end }}

<div id="daisy-sidebar-overlay" class="fixed inset-0 bg-black/50 z-[100] hidden transition-opacity duration-300 opacity-0"></div>
<div id="daisy-sidebar-panel" class="fixed top-0 {{ $sideClass }} h-full w-80 bg-base-200 z-[101] transform {{ $transClass }} transition-transform duration-300 shadow-xl flex flex-col" data-side="{{ $side }}">
    <div class="p-4 flex justify-between items-center border-b border-base-300 flex-none">
        <span class="text-xl font-bold">Menu</span>
        <button id="daisy-sidebar-close" class="btn btn-ghost btn-circle">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
    </div>
    <div class="flex-1 overflow-y-auto">
        <ul class="menu p-4 w-full text-base-content">
            {{ range .items }}
            <li><a href="{{ .url }}" class="text-lg">{{ .label }}</a></li>
            {{ end }}
        </ul>
    </div>
    {{ if .sidebarFooterBlocks }}
    <div class="p-4 border-t border-base-300 flex-none bg-base-100">
        {{ range .sidebarFooterBlocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </div>
    {{ end }}
</div>

<script>
    (function() {
        // Sidebar Logic
        const checkbox = document.getElementById('daisy-sidebar-checkbox');
        const overlay = document.getElementById('daisy-sidebar-overlay');
        const panel = document.getElementById('daisy-sidebar-panel');
        const close = document.getElementById('daisy-sidebar-close');
        
        function openSidebar() {
            if(!panel) return;
            const side = panel.dataset.side || 'left';
            const transClass = side === 'right' ? 'translate-x-full' : '-translate-x-full';
            
            overlay.classList.remove('hidden');
            setTimeout(() => {
                overlay.classList.remove('opacity-0');
                panel.classList.remove(transClass);
            }, 10);
            
            if (checkbox) checkbox.checked = true;
        }
        
        function closeSidebar() {
            if(!panel) return;
            const side = panel.dataset.side || 'left';
            const transClass = side === 'right' ? 'translate-x-full' : '-translate-x-full';
            
            overlay.classList.add('opacity-0');
            panel.classList.add(transClass);
            setTimeout(() => {
                overlay.classList.add('hidden');
            }, 300);
            
            if (checkbox) checkbox.checked = false;
        }
        
        if(checkbox) {
            checkbox.addEventListener('change', (e) => {
                if(e.target.checked) openSidebar();
                else closeSidebar();
            });
        }
        
        if(close) close.addEventListener('click', closeSidebar);
        if(overlay) overlay.addEventListener('click', closeSidebar);
    })();
</script>
{{ end }}
"""

        menu_dispatcher = """{{ $theme := site.Params.theme_preset | default "default" }}
{{ $templateDir := "default" }}
{{ if ne $theme "default" }}
    {{ $templateDir = "daisy" }}
{{ end }}
{{ partial (printf "themes/%s/menu.html" $templateDir) . }}"""

        # Write Menu files (Now that templates are defined)
        with open(blocks / 'menu.html', 'w') as f: f.write(menu_dispatcher)
        with open(daisy_theme_dir / 'menu.html', 'w') as f: f.write(daisy_menu)
        with open(default_theme_dir / 'menu.html', 'w') as f: f.write(default_menu)
        
        # Write daisy theme versions (using existing DaisyUI templates)
        with open(daisy_theme_dir / 'google_reviews.html', 'w') as f: f.write(google_reviews_tpl)
        with open(daisy_theme_dir / 'accordion.html', 'w') as f: f.write(accordion_tpl)
        with open(daisy_theme_dir / 'stats_counter.html', 'w') as f: f.write(stats_counter_tpl)
        with open(daisy_theme_dir / 'gallery.html', 'w') as f: f.write(gallery_tpl)
        with open(daisy_theme_dir / 'social_links.html', 'w') as f: f.write(daisy_social_links)
        with open(daisy_theme_dir / 'menu.html', 'w') as f: f.write(daisy_menu)
        with open(default_theme_dir / 'menu.html', 'w') as f: f.write(default_menu)
        
        # Write non-themed blocks directly
        with open(blocks / 'text.html', 'w') as f: f.write(text_tpl)
        with open(blocks / 'brand_logo.html', 'w') as f: f.write(brand_logo_tpl)
        
        # Write generic fallback ONLY for truly unknown ones
        for name in ['embed', 'cta_hero', 'faq', 'flip_cards', 'process_steps']:
              if not (blocks / f'{name}.html').exists():
                  with open(blocks / f'{name}.html', 'w') as f: f.write(f'<div class="{name}">{{{{ . | jsonify }}}}</div>')
        
        # Write generic fallback for others if they don't exist
        for name in ['text', 'gallery', 'stats', 'embed', 'cta_hero', 'social_links', 'faq', 'google_reviews', 'flip_cards', 'process_steps']:
                 with open(blocks / f'{name}.html', 'w') as f: f.write(f'<div class="{name}">{{{{ . | jsonify }}}}</div>')

        # Compile Handlebars blocks (overwriting hardcoded ones if match)
        print("DEBUG: Compiling Handlebars templates...")
        src_blocks = Path(settings.BASE_DIR) / 'hugo' / 'templates' / 'blocks'
        dest_blocks = output_dir / 'layouts' / 'partials' / 'blocks'
        TemplateCompiler.compile_all(src_blocks, dest_blocks)




    def _build_page_dict(self, page):
        # Build dictionary structure for the page
        data = {
            'title': page.title,
            'draft': page.status != 'published'
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
                        'block_type': 'row',
                        'flex_mode': True,
                        'gap': "2",
                        'blocks': [] # Will hold columns or content
                    }
                    
                    # Force responsive flex behavior: stack on mobile, row on desktop (no wrap)
                    # flex-nowrap is crucial because explicit widths (flex-basis) + gap > 100% causes wrapping without it
                    fc_classes = ['flex-col', 'md:flex-row', 'md:flex-nowrap']
                    if block.params.get('css_classes'):
                        fc_classes.append(block.params['css_classes'])
                    row_block['css_classes'] = ' '.join(fc_classes)
                        
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
                                'block_type': 'column',
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
                block_data['id'] = str(block.id) # Inject ID as string for unique element targeting (e.g. accordion groups)
                block_data['block_type'] = block.definition.id

                
                # Helper to fix image paths (uploads/ -> /media/uploads/)
                def sanitize_url(url):
                    if not url or not isinstance(url, str): return url
                    if url.startswith('http') or url.startswith('/') or url.startswith('data:'):
                        return url
                    # Assume relative paths meant for media (especially uploads) need prefix
                    # We specifically target 'uploads/' but can be broader if needed
                    if url.startswith('uploads/') or '.' in url: # simplistic check for file path
                         return f"/media/{url}"
                    return url

                # Sanitize top-level image fields
                for field in ['image', 'bg_image', 'bgImage', 'logo_image', 'src']:
                    if field in block_data:
                        block_data[field] = sanitize_url(block_data[field])
                
                # Sanitize lists
                if 'items' in block_data: # Menu, Features
                    for item in block_data['items']:
                        if 'image' in item: item['image'] = sanitize_url(item['image'])
                
                if 'images' in block_data: # Gallery
                    for img in block_data['images']:
                        if 'src' in img: img['src'] = sanitize_url(img['src'])

                if 'reviews' in block_data: # Google Reviews
                    for rev in block_data['reviews']:
                        if 'image' in rev: rev['image'] = sanitize_url(rev['image'])

                # Recurse children
                children = BlockInstance.objects.filter(parent=block).order_by('sort_order')
                if children.exists():
                    block_data['blocks'] = build_blocks(children)
                    
                if block.definition.id == 'carousel':
                    # Process JSON slides from params
                    raw_slides = block_data.get('slides', [])
                    processed_slides = []
                    
                    for slide in raw_slides:
                        processed_children = []
                        for child in slide.get('children', []):
                            # Child is a dict {type: '...', params: {...}}
                            child_data = child.get('params', {}).copy()
                            child_data['block_type'] = child.get('type')
                            child_data['id'] = child.get('id', str(uuid.uuid4()))
                            
                            # Sanitize child params
                            for field in ['image', 'bg_image', 'bgImage', 'logo_image', 'src']:
                                if field in child_data:
                                    child_data[field] = sanitize_url(child_data[field])
                            
                            processed_children.append(child_data)
                            
                        processed_slides.append({
                            'id': slide.get('id'),
                            'children': processed_children
                        })
                    
                    block_data['slides'] = processed_slides

                    
                out_blocks.append(block_data)
                
            return out_blocks

        # Build Zones
        # Combine page-specific and global blocks for header/footer
        # Main content is always page-specific
        from django.db.models import Q
        
        # Helper to get combined blocks for a zone
        def get_zone_blocks(zone_name):
            return BlockInstance.objects.filter(
                website=page.website,
                placement_key=zone_name
            ).filter(
                Q(page=page) | Q(page__isnull=True)
            ).order_by('sort_order')

        header = get_zone_blocks('header')
        main = page.main_blocks.filter(placement_key='main').order_by('sort_order')
        footer = get_zone_blocks('footer')
        
        # Flatten params to root level to ensure .Params.main_blocks works
        if header.exists(): data['header_blocks'] = build_blocks(header)
        if main.exists(): data['main_blocks'] = build_blocks(main)
        if footer.exists(): data['footer_blocks'] = build_blocks(footer)
        
        return data
        

    
    def compile_css(self, static_dir, website):
        """Compile Tailwind CSS - theme will be auto-detected from HTML"""
        from django.core.management import call_command
        
        theme = website.theme_preset
        # Print to server logs
        print(f"DEBUG: Compiling Tailwind CSS (theme '{theme}' will be auto-detected from HTML)...")
        
        try:
            # Run tailwind build command directly in-process
            # This avoids spawning a new python process and issues with paths/envs
            call_command('tailwind', 'build')
            
            print("DEBUG: CSS compiled successfully")
            self.stdout.write(self.style.SUCCESS(f"CSS compiled successfully"))
        except Exception as e:
            print(f"ERROR: Tailwind build failed: {str(e)}")
            self.stdout.write(self.style.WARNING(f"Tailwind build warning: {str(e)}"))
        
        # Copy compiled CSS to Hugo static directory
        theme_css = Path(settings.BASE_DIR) / 'theme' / 'static' / 'css' / 'dist' / 'styles.css'
        if theme_css.exists():
            css_dir = static_dir / 'css'
            css_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(theme_css, css_dir / 'styles.css')
            self.stdout.write(self.style.SUCCESS("Compiled CSS copied to Hugo output."))
        else:
            self.stdout.write(self.style.ERROR(f"Compiled CSS not found at {theme_css}"))

    def run_hugo_build(self, output_dir):
        """Run Hugo build to generate hugo_stats.json"""
        import subprocess
        
        self.stdout.write("Running Hugo build to generate hugo_stats.json...")
        
        hugo_bin = Path(settings.BASE_DIR) / 'bin' / 'hugo'
        if not hugo_bin.exists():
            self.stdout.write(self.style.ERROR(f"Hugo binary not found at {hugo_bin}"))
            return

        result = subprocess.run(
            [str(hugo_bin), '--source', str(output_dir), '--cleanDestinationDir'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.stdout.write(self.style.WARNING(f"Hugo build warning: {result.stderr}"))
        else:
            self.stdout.write(self.style.SUCCESS("Hugo build completed - hugo_stats.json generated"))
            
        # Verify hugo_stats.json was created
        stats_file = output_dir / 'hugo_stats.json'
        if stats_file.exists():
            self.stdout.write(self.style.SUCCESS(f"✓ hugo_stats.json found at {stats_file}"))
        else:
            self.stdout.write(self.style.ERROR(f"✗ hugo_stats.json NOT found at {stats_file}"))
