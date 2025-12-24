import re
import shlex
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class TemplateCompiler:
    @staticmethod
    def split_tag(content):
        try:
            # Handle leading/trailing parentheses if they are passed in
            content = content.strip()
            if content.startswith('(') and content.endswith(')'):
                content = content[1:-1].strip()
            return shlex.split(content)
        except ValueError:
            return content.split()

    @staticmethod
    def compile_source(source):
        # 0. Handle Triple Braces {{{ content }}} -> {{ content | safeHTML }}
        def triple_stash_replacer(match):
            content = match.group(1).strip()
            parts = TemplateCompiler.split_tag(content)
            
            if not parts: return match.group(0)

            # Handle helper inside triple stash: {{{ icon name }}}
            if parts[0] == 'icon':
                 if len(parts) >= 2:
                     icon_name = parts[1]
                     return f'{{{{ partial "helpers/icon.html" (dict "name" "{icon_name}") | safeHTML }}}}'
            
            # Handle renderStars: {{{ renderStars rating }}}
            if parts[0] == 'renderStars':
                 if len(parts) >= 2:
                     return f'{{{{ partial "helpers/stars.html" (dict "rating" .{parts[1]}) | safeHTML }}}}'
            
            # Handle markdownify: {{{ markdownify md }}} -> {{ .md | markdownify }}
            if parts[0] == 'markdownify':
                 if len(parts) >= 2:
                     return f'{{{{ .{parts[1]} | markdownify }}}}'
            
            # Generic case: {{{ var }}} -> {{ .var | safeHTML }}
            return f'{{{{ .{content} | safeHTML }}}}'
            
        safe_source = re.sub(r'\{\{\{\s*([^}]+)\s*\}\}\}', triple_stash_replacer, source)

        # 1. Handle {{#each var}} -> {{ range $index, $element := .var }}{{ with $element }}
        safe_source = re.sub(r'\{\{#each\s+([a-zA-Z0-9_.]+)\s*\}\}', r'{{ range $index, $element := .\1 }}{{ with $element }}', safe_source)
        
        # 2. Handle {{#if var}} -> {{ if .var }}
        safe_source = re.sub(r'\{\{#if\s+\.\./([a-zA-Z0-9_.]+)\s*\}\}', r'{{ if $.\1 }}', safe_source)
        safe_source = re.sub(r'\{\{#if\s+([a-zA-Z0-9_.]+)\s*\}\}', r'{{ if .\1 }}', safe_source)
        
        # 2b. Handle {{#unless var}} -> {{ if not .var }}
        safe_source = re.sub(r'\{\{#unless\s+([a-zA-Z0-9_.]+)\s*\}\}', r'{{ if not .\1 }}', safe_source)

        # 2c. Handle {{#if (eq var "value")}} -> {{ if eq .var "value" }}
        def if_helper_replacer(match):
            content = match.group(1).strip()
            parts = TemplateCompiler.split_tag(content)
            if not parts: return match.group(0)
            
            if parts[0] == 'eq':
                if len(parts) >= 3:
                    var_name = parts[1]
                    val = parts[2]
                    # Ensure val is quoted if it's a string literal and shlex stripped it
                    if not (val.startswith('"') or val.startswith("'")):
                        if not val.replace('.', '', 1).isdigit() and not (val.startswith('.') or val.startswith('$')):
                            val = f'"{val}"'
                    # Convert single quotes to double quotes for Hugo
                    val = val.replace("'", '"')
                    # Ensure var_name starts with dot if it doesn't start with $ or .
                    if not var_name.startswith('.') and not var_name.startswith('$'):
                        var_name = f'.{var_name}'
                    return f'{{{{ if eq {var_name} {val} }}}}'
            return f'{{{{ if {content} }}}}' 

        safe_source = re.sub(r'\{\{#if\s+(\([^}]+\))\s*\}\}', if_helper_replacer, safe_source)
        # Handle {{else if ...}}
        safe_source = re.sub(r'\{\{(?:#)?else\s+if\s+(\([^}]+\))\s*\}\}', lambda m: if_helper_replacer(m).replace('{{ if', '{{ else if'), safe_source)
        
        # 3. Handle {{/each}} -> {{ end }}{{ end }} (closes with and range)
        safe_source = re.sub(r'\{\{/each\}\}', r'{{ end }}{{ end }}', safe_source)
        
        # 3b. Handle {{/if}}, {{/unless}} -> {{ end }}
        safe_source = re.sub(r'\{\{/(if|unless)\}\}', r'{{ end }}', safe_source)
        
        # 4. Handle simple variables {{ var }} -> {{ .var }}
        def var_replacer(match):
            content = match.group(1).strip()
            parts = TemplateCompiler.split_tag(content)
            if not parts: return match.group(0)
            
            # Helper: add @index 1
            if parts[0] == 'add':
                args_out = []
                for p in parts[1:]:
                    if p == '@index': args_out.append('$index')
                    elif p.isdigit(): args_out.append(p)
                    elif p.startswith('.'): args_out.append(p)
                    else: args_out.append(f'.{p}')
                return f'{{{{ add {" ".join(args_out)} }}}}'
                
            if parts[0] == 'charAt':
                 return f'{{{{ substr .{parts[1]} {parts[2]} 1 }}}}'
            
            # Helper: render_block var -> {{ partial "blocks/render-block.html" .var }}
            if parts[0] == 'render_block':
                var_name = parts[1] if len(parts) > 1 else '.'
                if not var_name.startswith('.') and not var_name.startswith('$') and var_name != 'this':
                    var_name = f'.{var_name}'
                if var_name == 'this': var_name = '.'
                return f'{{{{ partial "blocks/render-block.html" {var_name} }}}}'

            # Helper: default var defaultValue
            # Handlebars: {{default var "val"}} -> Hugo: {{ default "val" .var }}
            if parts[0] == 'default':
                if len(parts) >= 3:
                    var_name = parts[1]
                    default_val = parts[2]
                    # Add dot prefix to variable if it doesn't start with one
                    if not var_name.startswith('.') and not var_name.startswith('$'):
                        var_name = f'.{var_name}'
                    
                    # Convert single quotes to double quotes for Hugo
                    default_val = default_val.replace("'", '"')
                    
                    # Re-quote string literals if they are not already quoted and not variables/numbers
                    if not (default_val.startswith('"') or default_val.startswith("'")):
                        if not default_val.replace('.', '', 1).isdigit() and not (default_val.startswith('.') or default_val.startswith('$')):
                            default_val = f'"{default_val}"'
                    
                    # Correct Hugo order: default DEFAULT_VAL INPUT
                    return f'{{{{ default {default_val} {var_name} }}}}'

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
