import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class TemplateCompiler:
    @staticmethod
    def compile_source(source):
        # 1. Handle {{#each var}} -> {{ range .var }}
        safe_source = re.sub(r'\{\{#each\s+([a-zA-Z0-9_]+)\s*\}\}', r'{{ range .\1 }}', source)
        
        # 2. Handle {{#if var}} -> {{ if .var }}
        safe_source = re.sub(r'\{\{#if\s+([a-zA-Z0-9_]+)\s*\}\}', r'{{ if .\1 }}', safe_source)
        
        # 3. Handle {{/if}} and {{/each}} -> {{ end }}
        safe_source = re.sub(r'\{\{/(if|each)\}\}', r'{{ end }}', safe_source)
        
        # 4. Handle simple variables {{ var }} -> {{ .var }}
        # We must exclude {{ if ... }}, {{ range ... }}, {{ end }}, {{ partial ... }}
        # Strategy: Match generic {{ var }} and check if 'var' is a keyword or starts with .
        def var_replacer(match):
            content = match.group(1).strip()
            # If it already starts with . or is a keyword/helper, leave it (approximate check)
            if content.startswith('.') or content.startswith('if ') or content.startswith('range ') or content == 'end' or content.startswith('partial '):
                return match.group(0)
            
            # Special case: {{ this }} -> {{ . }}
            if content == 'this':
                return '{{ . }}'
                
            return f'{{{{ .{content} }}}}'

        safe_source = re.sub(r'\{\{\s*([^}]+)\s*\}\}', var_replacer, safe_source)
        
        return safe_source

    @staticmethod
    def compile_all(src_dir, dest_dir):
        src_path = Path(src_dir)
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for hbs_file in src_path.glob('*.hbs'):
            try:
                content = hbs_file.read_text(encoding='utf-8')
                compiled = TemplateCompiler.compile_source(content)
                
                dest_file = dest_path / (hbs_file.stem + '.html')
                dest_file.write_text(compiled, encoding='utf-8')
                count += 1
            except Exception as e:
                print(f"Error compiling {hbs_file}: {e}")
                
        return count

class Command(BaseCommand):
    help = 'Compiles Handlebars templates in hugo/templates/blocks to Hugo partials'

    def handle(self, *args, **options):
        src = Path(settings.BASE_DIR) / 'hugo' / 'templates' / 'blocks'
        dest = Path(settings.BASE_DIR) / 'hugo_output' / 'layouts' / 'partials' / 'blocks'
        
        self.stdout.write(f"Compiling templates from {src} to {dest}...")
        count = TemplateCompiler.compile_all(src, dest)
        self.stdout.write(self.style.SUCCESS(f"Successfully compiled {count} templates."))
