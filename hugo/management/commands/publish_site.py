
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
        self.generate_layouts(output_dir, website)
        self.generate_fixed_templates(output_dir) # Overwrite with fixed ones if needed

        # 3. Generate Pages (Using ORIGINAL views.py logic)
        self.generate_pages_original(website, content_dir)
        
        # 4. Copy Media (The Fix)
        self.copy_media(website, static_dir)
        
        # 5. Compile and Copy Tailwind CSS (with selected theme)
        self.compile_css(static_dir, website)
        
        self.stdout.write(self.style.SUCCESS(f"Site generated in {output_dir}"))

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
    <div data-theme="{theme}" style="background: #333; color: #fff; padding: 10px; font-family: monospace; z-index: 9999; position: relative;">
        <strong>DEBUG INFO:</strong> <span class="badge badge-primary">Theme: {theme}</span><br>
        Theme Preset: [{{{{ site.Params.theme_preset }}}}]<br>
    </div>
    {{{{ block "main" . }}}}{{{{ end }}}}
</body>
</html>"""
            f.write(baseof)
        
        # Single/List
        single = """{{ define "main" }}
<div class="flex flex-col min-h-screen">
    <header class="w-full border-b bg-base-100 border-base-300">
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
    <h2 class="text-3xl font-bold text-center mb-10 text-base-content">{{ .title }}</h2>
    {{ end }}
    <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {{ range .items }}
        <div class="group bg-base-100 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border border-base-300 flex flex-col h-full">
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
        {{ range .features }}
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
        <div class="card card-compact bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300">
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
        section_tpl = """<div class="section py-12 {{ .css_classes }}">
    <div class="container mx-auto px-4">
        {{ range .blocks }}
            {{ partial "blocks/render-block.html" . }}
        {{ end }}
    </div>
</div>"""

        row_tpl = """<div class="flex flex-wrap {{ if .gap }}gap-{{ .gap }}{{ else }}gap-4{{ end }} {{ .justify | default "justify-start" }} {{ .align | default "items-start" }} {{ .css_classes }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>"""

        column_tpl = """<div class="flex-1 {{ .css_classes }}" style="{{ if .width_percent }}flex-basis: {{ .width_percent }}%;{{ end }}">
    {{ range .blocks }}
        {{ partial "blocks/render-block.html" . }}
    {{ end }}
</div>"""

        with open(blocks / 'section.html', 'w') as f: f.write(section_tpl)
        with open(blocks / 'row.html', 'w') as f: f.write(row_tpl)
        with open(blocks / 'column.html', 'w') as f: f.write(column_tpl)
        
        # --- CONTENT BLOCKS ---
        hero_tpl = """<div class="relative overflow-hidden w-full {{ .css_classes }}">
    <img src="{{ .bg_image }}" alt="{{ .title }}" class="w-full h-64 md:h-96 object-cover" loading="eager">
    <div class="absolute inset-0 bg-black/40 flex flex-col items-center justify-center text-center px-4">
        <div class="container mx-auto">
            <h1 class="text-3xl md:text-5xl font-bold text-white mb-4 drop-shadow-lg">{{ .title }}</h1>
            <p class="text-lg md:text-xl text-white/90 max-w-2xl mx-auto drop-shadow">{{ .subtitle }}</p>
            {{ if .cta_url }}
            <a href="{{ .cta_url }}" class="btn btn-primary inline-block mt-6 px-8 py-3 rounded-full font-semibold shadow-lg transition-all hover:scale-105">{{ .cta_text }}</a>
            {{ end }}
        </div>
    </div>
</div>"""

        markdown_tpl = """<div class="prose max-w-none py-6 {{ .css_classes }}">
    {{ .content | markdownify }}
</div>"""

        button_tpl = """<div class="mb-4 {{ .css_classes }}">
    <a href="{{ .url }}" class="btn btn-primary inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 no-underline px-6 py-3 text-base shadow-md hover:shadow-lg">{{ .text }}</a>
</div>"""

        accordion_tpl = """<div class="space-y-2 {{ .css_classes }}">
    {{ range .items }}
    <details class="group bg-base-100 rounded-lg shadow-md overflow-hidden border border-base-300">
        <summary class="cursor-pointer p-6 font-semibold text-base-content hover:bg-base-200 transition-colors flex items-center justify-between list-none">
            <span>{{ .title }}</span>
            <svg class="w-5 h-5 opacity-60 transform transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
        </summary>
        <div class="px-6 pb-6 opacity-80 border-t border-base-300 pt-4">
            {{ .content | markdownify }}
        </div>
    </details>
    {{ end }}
</div>"""

        quote_tpl = """<blockquote class="border-l-4 border-indigo-500 pl-4 py-2 mb-8 italic text-slate-700 {{ .css_classes }}">
    <p class="text-lg">"{{ .text }}"</p>
    {{ if .author }}<cite class="block mt-2 text-sm font-semibold text-slate-900">- {{ .author }}</cite>{{ end }}
</blockquote>"""

        image_tpl = """<figure class="mb-8 {{ .css_classes }}" style="width: 100%; margin: 0 auto;">
    <img src="{{ .src }}" alt="{{ .alt }}" class="w-full rounded-lg shadow-md" style="height: auto; object-fit: cover;">
    {{ if .caption }}<figcaption class="text-center text-sm text-slate-500 mt-2">{{ .caption }}</figcaption>{{ end }}
</figure>"""

        carousel_tpl = """<div class="carousel-container py-8 {{ .css_classes }}" 
     data-carousel-id="{{ now.UnixNano }}"
     data-auto-advance="{{ .auto_advance | default true }}"
     data-interval="{{ .interval_seconds | default 5 }}">
    {{ if .slides }}
    <div class="relative" style="display: grid; grid-template-areas: 'stack'; place-items: center; min-height: 300px; overflow: hidden;">
        {{ range $index, $slide := .slides }}
        <div class="carousel-slide" data-slide-index="{{ $index }}" style="grid-area: stack; width: 85%; max-width: 900px; transition: transform 0.5s ease-in-out, opacity 0.5s ease-in-out; transform: translateX({{ if eq $index 0 }}0{{ else }}100%{{ end }}); opacity: {{ if eq $index 0 }}1{{ else }}0{{ end }}; pointer-events: {{ if eq $index 0 }}auto{{ else }}none{{ end }};">
            <div class="bg-white rounded-lg shadow-md p-6">
                {{ range $slide.children }}
                    {{ partial "blocks/render-block.html" . }}
                {{ end }}
            </div>
        </div>
        {{ end }}
        
        {{ if gt (len .slides) 1 }}
        <button data-carousel-prev style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); z-index: 10;" class="w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all bg-slate-100/80 hover:bg-slate-200 border border-slate-200 backdrop-blur">
            <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
        </button>
        <button data-carousel-next style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); z-index: 10;" class="w-12 h-12 rounded-full flex items-center justify-center cursor-pointer transition-all bg-slate-100/80 hover:bg-slate-200 border border-slate-200 backdrop-blur">
            <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
        </button>
        {{ end }}
    </div>
    
    {{ if gt (len .slides) 1 }}
    <div class="flex justify-center gap-3 mt-6">
        {{ range $index, $slide := .slides }}
        <button data-carousel-dot="{{ $index }}" class="transition-all duration-200 border-0 cursor-pointer p-0" style="width:{{ if eq $index 0 }}32px{{ else }}12px{{ end }}; border-radius: {{ if eq $index 0 }}6px{{ else }}50%{{ end }}; background: {{ if eq $index 0 }}var(--color-primary, #6366f1){{ else }}#e2e8f0{{ end }}; height: 12px;"></button>
        {{ end }}
    </div>
    {{ end }}
    
<script>
(function() {
    const container = document.querySelector('[data-carousel-id="{{ now.UnixNano }}"]');
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
                dot.style.width = '32px';
                dot.style.borderRadius = '6px';
                dot.style.background = 'var(--color-primary, #6366f1)';
            } else {
                dot.style.width = '12px';
                dot.style.borderRadius = '50%';
                dot.style.background = '#e2e8f0';
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

        with open(blocks / 'hero.html', 'w') as f: f.write(hero_tpl)
        with open(blocks / 'markdown.html', 'w') as f: f.write(markdown_tpl)
        with open(blocks / 'button.html', 'w') as f: f.write(button_tpl)
        with open(blocks / 'accordion.html', 'w') as f: f.write(accordion_tpl)
        with open(blocks / 'quote.html', 'w') as f: f.write(quote_tpl)
        with open(blocks / 'image.html', 'w') as f: f.write(image_tpl)
        with open(blocks / 'carousel.html', 'w') as f: f.write(carousel_tpl)
        
        # --- ADDITIONAL BLOCK TEMPLATES ---
        text_tpl = """<div class="prose max-w-none py-6 {{ .css_classes }}">
    {{ .content | markdownify }}
</div>"""

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
            {{ range .items }}
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

        social_links_tpl = """<div class="flex flex-wrap justify-center gap-4 py-6 {{ .css_classes }}">
    {{ range .links }}
    <a href="{{ .url }}" target="_blank" rel="noopener noreferrer" 
       class="w-12 h-12 rounded-full bg-slate-100 hover:bg-indigo-600 hover:text-white flex items-center justify-center text-slate-600 font-bold transition-all duration-200 shadow-sm hover:shadow-md">
        {{ if in .platform "instagram" }}IG
        {{ else if in .platform "facebook" }}FB
        {{ else if in .platform "twitter" }}TW
        {{ else if in .platform "linkedin" }}LI
        {{ else }}🔗{{ end }}
    </a>
    {{ end }}
</div>"""

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
            {{ range .items }}
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

        # Write dispatchers to blocks/
        with open(blocks / 'google_reviews.html', 'w') as f: f.write(google_reviews_dispatcher)
        with open(blocks / 'accordion.html', 'w') as f: f.write(accordion_dispatcher)
        with open(blocks / 'stats.html', 'w') as f: f.write(stats_dispatcher)
        with open(blocks / 'stats_counter.html', 'w') as f: f.write(stats_dispatcher)
        with open(blocks / 'gallery.html', 'w') as f: f.write(gallery_dispatcher)
        
        # Write default theme versions
        with open(default_theme_dir / 'google_reviews.html', 'w') as f: f.write(default_google_reviews)
        with open(default_theme_dir / 'accordion.html', 'w') as f: f.write(default_accordion)
        with open(default_theme_dir / 'stats_counter.html', 'w') as f: f.write(default_stats)
        with open(default_theme_dir / 'gallery.html', 'w') as f: f.write(default_gallery)
        
        # Write daisy theme versions (using existing DaisyUI templates)
        with open(daisy_theme_dir / 'google_reviews.html', 'w') as f: f.write(google_reviews_tpl)
        with open(daisy_theme_dir / 'accordion.html', 'w') as f: f.write(accordion_tpl)
        with open(daisy_theme_dir / 'stats_counter.html', 'w') as f: f.write(stats_counter_tpl)
        with open(daisy_theme_dir / 'gallery.html', 'w') as f: f.write(gallery_tpl)
        
        # Write non-themed blocks directly
        with open(blocks / 'text.html', 'w') as f: f.write(text_tpl)
        with open(blocks / 'social_links.html', 'w') as f: f.write(social_links_tpl)
        
        # Write generic fallback ONLY for truly unknown ones
        for name in ['embed', 'cta_hero', 'faq', 'flip_cards', 'process_steps']:
              if not (blocks / f'{name}.html').exists():
                  with open(blocks / f'{name}.html', 'w') as f: f.write(f'<div class="{name}">{{{{ . | jsonify }}}}</div>')
        
        menu_tpl = """{{ $position := .position | default "normal" }}
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
        
        with open(blocks / 'menu.html', 'w') as f: f.write(menu_tpl)

        # Write generic fallback for others if they don't exist
        for name in ['text', 'gallery', 'stats', 'embed', 'cta_hero', 'social_links', 'faq', 'google_reviews', 'flip_cards', 'process_steps']:
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
    
    def compile_css(self, static_dir, website):
        """Compile Tailwind CSS - theme will be auto-detected from HTML"""
        import subprocess
        
        theme = website.theme_preset
        self.stdout.write(f"Compiling Tailwind CSS (theme '{theme}' will be auto-detected from HTML)...")
        
        # Run tailwind build command - it will scan the Hugo output and detect the theme
        result = subprocess.run(
            ['./venv/bin/python', 'manage.py', 'tailwind', 'build'],
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.stdout.write(self.style.WARNING(f"Tailwind build warning: {result.stderr}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"CSS compiled successfully"))
        
        # Copy compiled CSS to Hugo static directory
        theme_css = Path(settings.BASE_DIR) / 'theme' / 'static' / 'css' / 'dist' / 'styles.css'
        if theme_css.exists():
            css_dir = static_dir / 'css'
            css_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(theme_css, css_dir / 'styles.css')
            self.stdout.write(self.style.SUCCESS("Compiled CSS copied to Hugo output."))
        else:
            self.stdout.write(self.style.ERROR(f"Compiled CSS not found at {theme_css}"))

