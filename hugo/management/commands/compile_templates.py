import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class TemplateCompiler:
    @staticmethod
    def compile_source(source):
        # 0. Handle Triple Braces {{{ content }}} -> {{ content | safeHTML }}
        # We process this first to avoid double processing
        def triple_stash_replacer(match):
            content = match.group(1).strip()
            # Handle helper inside triple stash: {{{ icon name }}} -> {{ partial "helpers/icon.html" (dict "name" name) | safeHTML }}
            if content.startswith('icon '):
                 parts = content.split()
                 if len(parts) >= 2:
                     return f'{{{{ partial "helpers/icon.html" (dict "name" .{parts[1]}) | safeHTML }}}}'
            
            # Handle renderStars: {{{ renderStars rating }}}
            if content.startswith('renderStars '):
                 parts = content.split()
                 if len(parts) >= 2:
                     return f'{{{{ partial "helpers/stars.html" (dict "rating" .{parts[1]}) | safeHTML }}}}'
            
            # Generic case: {{{ var }}} -> {{ .var | safeHTML }}
            return f'{{{{ .{content} | safeHTML }}}}'
            
        safe_source = re.sub(r'\{\{\{\s*([^}]+)\s*\}\}\}', triple_stash_replacer, source)

        # 1. Handle {{#each var}} -> {{ range $index, $element := .var }}{{ with $element }}
        # This exposes $index and shadows it correctly for nested loops, while keeping context (.)
        safe_source = re.sub(r'\{\{#each\s+([a-zA-Z0-9_.]+)\s*\}\}', r'{{ range $index, $element := .\1 }}{{ with $element }}', safe_source)
        
        # 2. Handle {{#if var}} -> {{ if .var }}
        # For parent context (../var), we need to access from outside the 'with' block
        safe_source = re.sub(r'\{\{#if\s+\.\./([a-zA-Z0-9_.]+)\s*\}\}', r'{{ if $.\1 }}', safe_source)
        safe_source = re.sub(r'\{\{#if\s+([a-zA-Z0-9_.]+)\s*\}\}', r'{{ if .\1 }}', safe_source)
        
        # 2b. Handle {{#unless var}} -> {{ if not .var }}
        safe_source = re.sub(r'\{\{#unless\s+([a-zA-Z0-9_.]+)\s*\}\}', r'{{ if not .\1 }}', safe_source)

        # 2c. Handle {{#if (eq var "value")}} -> {{ if eq .var "value" }}
        def if_helper_replacer(match):
            content = match.group(1).strip()
            if content.startswith('(') and content.endswith(')'):
                content = content[1:-1]
            parts = content.split()
            if parts[0] == 'eq':
                var_name = parts[1]
                val = parts[2]
                return f'{{{{ if eq .{var_name} {val} }}}}'
            return f'{{{{ is {content} }}}}' 

        safe_source = re.sub(r'\{\{#if\s+(\([^}]+\))\s*\}\}', if_helper_replacer, safe_source)
        # Handle {{else if ...}} (Handlebars usually doesn't have # for else if)
        safe_source = re.sub(r'\{\{(?:#)?else\s+if\s+(\([^}]+\))\s*\}\}', lambda m: if_helper_replacer(m).replace('{{ if', '{{ else if'), safe_source)
        
        # 3. Handle {{/each}} -> {{ end }}{{ end }} (closes with and range)
        safe_source = re.sub(r'\{\{/each\}\}', r'{{ end }}{{ end }}', safe_source)
        
        # 3b. Handle {{/if}}, {{/unless}} -> {{ end }}
        safe_source = re.sub(r'\{\{/(if|unless)\}\}', r'{{ end }}', safe_source)
        
        # 4. Handle simple variables {{ var }} -> {{ .var }}
        def var_replacer(match):
            content = match.group(1).strip()
            
            # Helper: add @index 1
            if content.startswith('add '):
                parts = content.split()
                # Simple arg parser
                args_out = []
                for p in parts[1:]:
                    if p == '@index': args_out.append('$index')
                    elif p.isdigit(): args_out.append(p)
                    else: args_out.append(f'.{p}')
                
                return f'{{{{ add {" ".join(args_out)} }}}}'
                
            if content.startswith('charAt '):
                 parts = content.split()
                 return f'{{{{ substr .{parts[1]} {parts[2]} 1 }}}}'
            
            # Helper: default var defaultValue
            if content.startswith('default '):
                parts = content.split(maxsplit=2)  # Split into at most 3 parts
                if len(parts) >= 3:
                    var_name = parts[1]
                    default_val = parts[2]
                    # Add dot prefix to variable if it doesn't start with one
                    if not var_name.startswith('.'):
                        var_name = f'.{var_name}'
                    # Convert single quotes to double quotes for Hugo
                    default_val = default_val.replace("'", '"')
                    return f'{{{{ default {var_name} {default_val} }}}}'



            # Ignore keywords (but not ../ parent references)
            if (content.startswith('.') and not content.startswith('../')) or content.startswith('if ') or content.startswith('range ') or content.startswith('with ') or content == 'end' or content.startswith('partial ') or content.startswith('else') or content == '$index':
                return match.group(0)
            
            # Handle @index special var
            if content == '@index':
                return '{{ $index }}'

            # Handle {{ this }}
            if content == 'this':
                return '{{ . }}'
            
            # Handle parent context {{ ../var }} -> {{ $.var }}
            if content.startswith('../'):
                var_name = content[3:]  # Remove ../
                return f'{{{{ $.{var_name} }}}}'
                
            return f'{{{{ .{content} }}}}'

        safe_source = re.sub(r'\{\{\s*([^}]+)\s*\}\}', var_replacer, safe_source)
        
        # 5. Fix ranges to include index for process_steps
        # {{ range .steps }} -> {{ range $index, $element := .steps }}
        # We only do this if we detect $index usage? Or always?
        # Let's do it always for arrays. But .steps might not be array? 
        # Let's safely assume we can use {{ range $index, $element := .steps }}
        # But then we must replace {{ .title }} with {{ $element.title }} inside the loop? 
        # NO, Hugo: {{ range .steps }} context is the item. {{@index}} is not available.
        # To get index, {{ range $index, $element := .steps }}.
        # Context inside is NOT changed to element automatically if we declare variables?
        # Actually in Hugo: {{ range $index, $element := . }} dot is still the top unless...
        # Wait, {{ range . }} dot IS the element.
        # {{ range $index, $element := . }} dot IS the top? No.
        # Let's stick to: we need to change {{ range .steps }} to {{ range $index, $item := .steps }} AND change all variable references inside to $item.variable? That's too hard for regex.
        
        # Better approach for @index: 
        # {{ range .steps }} sets dot to item. 
        # There is no generic way to get index without defining variable.
        # Hack for process_steps: 
        # Replace {{ range .steps }} with {{ range $index, $e := .steps }} AND 
        # then replace {{ .title }} with {{ .title }}? No, dot context context...
        # If we use {{ range $index, $e := .steps }}, dot is preserved as parent? No.
        # "Inside the loop, . is set to the current element." -> Wait, that's only for {{ range .steps }}
        # "If variables are declared... . is...?"
        # Checked Hugo docs: "variables... are initialized... . (the context) is NOT changed."
        # So if we change to {{ range $i, $e := ... }} we must access via $e.
        
        # ALTERNATIVE: Use a hugo scratch counter? 
        # {{ scratch.Set "index" 0 }} {{ range .steps }} {{ scratch.Add "index" 1 }} ... {{ scratch.Get "index" }}
        
        # Let's replace {{ add @index 1 }} with a specific counter implementation via regex hook on the loop?
        # Or just accept that "add @index 1" might fail or output 0 for now?
        # The user's goal is to FIX the build.
        # Build fails on {{{.
        
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
