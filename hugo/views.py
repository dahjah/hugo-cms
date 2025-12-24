from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
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

from django.views.decorators.clickjacking import xframe_options_sameorigin

@xframe_options_sameorigin
def serve_preview_asset(request, website_id, path):
    """
    Serves static assets and HTML for preview.
    For HTML files, injects the CMS editor script.
    """
    from django.http import FileResponse, Http404, HttpResponse
    import mimetypes
    
    try:
        website = Website.objects.get(id=website_id)
        base_output_dir = Path(settings.BASE_DIR) / 'hugo_output' / website.slug / 'public'
        
        # 1. Resolve Path
        # Handle root or directory requests
        if not path or path.endswith('/'):
            target_path = path + 'index.html'
        else:
            target_path = path

        # Safe path joining
        # Remove leading slashes to prevent join from resetting root
        safe_target_path = target_path.lstrip('/')
        file_path = (base_output_dir / safe_target_path).resolve()
        
        # Security check: Ensure we are still inside base_output_dir
        if not str(file_path).startswith(str(base_output_dir.resolve())):
             # Additional check: prevent '..' fallback triggers if resolve is tricky
             raise Http404("Invalid path security")

        # Fallback: If path didn't end in slash but is a directory, try adding index.html
        if file_path.is_dir():
             file_path = file_path / 'index.html'
             
        if not file_path.exists() or not file_path.is_file():
             raise Http404(f"File not found: {path}")
             
        # Detect content type
        content_type, encoding = mimetypes.guess_type(file_path)
        content_type = content_type or 'application/octet-stream'
        
        # 2. HTML Injection (if applicable)
        if content_type == 'text/html':
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Inject Editor Helper Script
            # We inject a script that enables the "Click to Edit" postMessage bridge
            editor_script = """
            <script>
            (function() {
                // Editor Helper - Injected by CMS
                console.log("CMS Editor Connected");

                // Inject Styles for highlighting
                const style = document.createElement('style');
                style.textContent = `
                    [data-block-id] {
                        cursor: pointer;
                        transition: outline 0.1s;
                    }
                    [data-block-id]:hover {
                        outline: 2px solid rgba(99, 102, 241, 0.5) !important; 
                    }
                    .cms-selected-block {
                        outline: 3px solid #6366f1 !important;
                        position: relative;
                        z-index: 10;
                    }
                `;
                document.head.appendChild(style);
                
                document.body.addEventListener('click', function(e) {
                    // Find closest block
                    const block = e.target.closest('[data-block-id]');
                    if (block) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        const blockId = block.getAttribute('data-block-id');
                        console.log("Block Selected:", blockId);
                        
                        // Send message to parent
                        window.parent.postMessage({
                            type: 'block-selected',
                            blockId: blockId
                        }, '*');
                        
                        // Update visual selection
                        document.querySelectorAll('.cms-selected-block').forEach(el => el.classList.remove('cms-selected-block'));
                        block.classList.add('cms-selected-block');
                    }
                }, true);

                // Listen for messages from parent (e.g. to highlight block from sidebar)
                window.addEventListener('message', function(e) {
                     if (e.data && e.data.type === 'select-block') {
                         const blockId = e.data.blockId;
                         const block = document.querySelector(`[data-block-id="${blockId}"]`);
                         if (block) {
                             document.querySelectorAll('.cms-selected-block').forEach(el => el.classList.remove('cms-selected-block'));
                             block.classList.add('cms-selected-block');
                             block.scrollIntoView({ behavior: 'smooth', block: 'center' });
                         }
                     }
                });
            })();
            </script>
            """
            
            # Helper injection
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', f'{editor_script}</body>')
            else:
                html_content += editor_script
                
            # Base Tag Injection?
            # Ideally not needed if using iframe src, but if assets are relative, they should resolve relative to current URL.
            # Example: src="/api/sites/1/preview/about/" -> loads "about/index.html"
            # <link href="/css/style.css"> -> resolves to domain root /css/style.css which is wrong.
            # We need <base href="/api/sites/1/preview/">
            
            base_href = f"/api/sites/{website_id}/preview/"
            
            # Robust replacement using regex to handle single/double quotes
            import re
            
            # Force replace paths starting with /css, /js, /images/ /media
            # This handles root-relative paths that <base> doesn't catch
            # Matches src="/css/..." or href='/js/...'
            # We want to replace valid asset starts
            
            def replace_asset_link(match):
                attr = match.group(1) # href or src
                quote = match.group(2) # " or '
                path = match.group(3) # /css/ or /js/
                rest = match.group(4)
                return f'{attr}={quote}{base_href}{path.lstrip("/")}{rest}'

            # Regex Explanation:
            # (href|src)\s*=\s*  -> Attribute name
            # (["\'])            -> Quote char
            # (/((?:css|js|images|media)/.*?)) -> Path starting with / followed by standard asset folders
            # \2                 -> Matching closing quote
            
            # Simplified: Just look for usages of /css, /js, /media, /images inside href/src
            # And prepend base_href (without the double slash issue)
            
            # Pattern: (href|src)=["']/(css|js|images|media)/
            
            html_content = re.sub(
                r'(href|src)\s*=\s*(["\'])/(css|js|images|media)(.*?)["\']', 
                lambda m: f'{m.group(1)}={m.group(2)}{base_href}{m.group(3)}{m.group(4)}{m.group(2)}', 
                html_content
            )

            # Simple heuristic: inject base tag if one doesn't exist
            if '<base' not in html_content:
                if '<head>' in html_content:
                    html_content = html_content.replace('<head>', f'<head><base href="{base_href}">', 1)
                else:
                    html_content = f'<base href="{base_href}">' + html_content

            return HttpResponse(html_content, content_type=content_type)

        # 3. Serve Assets
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Http404(str(e))

def editor_view(request, website_id=None, page_id=None):
    """Serves the Vue.js frontend application."""
    if website_id:
        try:
            # Check if website exists
            Website.objects.get(id=website_id)
        except (Website.DoesNotExist, ValueError, ValidationError):
            # Invalid ID or website doesn't exist - redirect to root
            return redirect('editor')
            
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
        Uses the shared 'publish_site' management command and 'DeploymentOrchestrator'.
        """
        import os
        from django.core.management import call_command
        import io
        from django.shortcuts import get_object_or_404
        
        website_id = request.data.get('website_id')
        if not website_id:
             return Response({'error': 'website_id is required'}, status=400)
             
        website = get_object_or_404(Website, id=website_id)
        
        # 1. Generate Site
        out = io.StringIO()
        try:
            call_command('publish_site', website.slug, stdout=out)
        except Exception as e:
            return Response({'error': f"Site generation failed: {str(e)}", 'logs': out.getvalue()}, status=500)

        generation_log = out.getvalue()

        # 2. Deploy
        deploy_log = []
        deployed_url = None
        
        if website.deployment_provider:
            # Re-import to ensure fresh context
            from hugo.deployment_service import DeploymentOrchestrator
            
            orchestrator = DeploymentOrchestrator(website.deployment_provider, website)
            output_dir = os.path.join(settings.BASE_DIR, 'hugo_output', website.slug)
            
            try:
                deployment = orchestrator.deploy(output_dir)
                
                if deployment.status == 'success':
                    deployed_url = deployment.deployment_url
                    deploy_log.append(f"Deployment successful: {deployed_url}")
                    
                    # Update status for ALL pages
                    from django.utils import timezone
                    now = timezone.now()
                    website.pages.update(status='published', last_published_at=now)
                else:
                    deploy_log.append(f"Deployment failed: {deployment.error_message}")
                    if deployment.build_output:
                         deploy_log.append("Build Output:\\n" + deployment.build_output)
                    
                    return Response({
                        'status': 'error',
                        'error': deployment.error_message,
                        'generation_log': generation_log,
                        'deploy_log': "\\n".join(deploy_log)
                    }, status=500)
                    
            except Exception as e:
                import traceback
                return Response({
                    'status': 'error',
                    'error': f"Orchestrator exception: {str(e)}",
                    'generation_log': generation_log,
                    'traceback': traceback.format_exc()
                }, status=500)
        else:
            deploy_log.append("No deployment provider configured. Skipped deployment.")

        return Response({
            'success': True,
            'status': 'published',
            'generation_log': generation_log,
            'deploy_log': "\n".join(deploy_log),
            'deployed_url': deployed_url
        })
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
            page_content = self._generate_page_markdown(page, base_url=base_url)
            
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
            page.status = 'published'
            page.save(update_fields=['last_published_at', 'status'])

            # 2. Trigger Site Build (Incremental)
            # Pass website slug to command w/ keep_existing=True and page_id
            from django.core.management import call_command
            import io
            out = io.StringIO()
            
            # Use incremental build: 
            # - keep_existing=True: Don't wipe output dir.
            # - page_id: ONLY regenerate this page's MD. Preserve others as they were (Live state).
            call_command('publish_site', 
                website.slug, 
                keep_existing=True, 
                page_id=str(page.id),
                stdout=out
            )
            
            # 3. Deploy
            deploy_result = "Deployment skipped (no provider)"
            deployed_url = None
            
            if website.deployment_provider:
                from hugo.deployment_service import DeploymentOrchestrator
                orchestrator = DeploymentOrchestrator(website.deployment_provider, website)
                output_dir = Path(settings.BASE_DIR) / 'hugo_output' / website.slug
                
                deployment = orchestrator.deploy(output_dir)
                if deployment.status == 'success':
                    deployed_url = deployment.deployment_url
                    deploy_result = f"Deployed to: {deployed_url}"
                else:
                    return Response({
                        'success': False, 
                        'error': f"Deployment failed: {deployment.error_message}"
                    }, status=500)

            return Response({
                'success': True,
                'message': f'Published page: {page.title}. {deploy_result}',
                'file': str(page_file)
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    
    @action(detail=False, methods=['post'])
    def render_canvas(self, request):
        """
        Renders the true HTML for a page (preview) based on the request payload.
        Payload can include unsaved modifications to blocks and page metadata.
        """
        import json
        import subprocess
        from pathlib import Path
        from django.conf import settings
        
        try:
            data = request.data
            website_id = data.get('website_id')
            page_id = data.get('page_id')
            
            if not website_id:
                return Response({'error': 'website_id is required'}, status=400)

            website = Website.objects.get(id=website_id)
            
            # --- 1. Construct Mock Objects from Payload ---
            # We mimic the Django models structure so the existing generator works
            
            # Mock Page
            page_data = data.get('page', {})
            
            # If we have a real page ID, get it for base values, then override
            real_page = None
            if page_id:
                try:
                    real_page = Page.objects.get(id=page_id)
                except Page.DoesNotExist:
                    pass
            
            class MockPage:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            
            mock_page = MockPage(
                title=page_data.get('title', real_page.title if real_page else 'Untitled'),
                slug=page_data.get('slug', real_page.slug if real_page else '/temp-preview'),
                layout=page_data.get('layout', real_page.layout if real_page else 'single'),
                description=page_data.get('description', real_page.description if real_page else ''),
                date=page_data.get('date', real_page.date if real_page else ''),
                tags=page_data.get('tags', real_page.tags if real_page else []),
                website=website
            )

            # Mock Blocks
            # The payload 'blocks' should be a hierarchical list of blocks
            # We need to flatten them into a list of BlockInstance-like objects with 'parent' pointers if the generator expects that
            # BUT: _generate_page_markdown just iterates root blocks and calls render_blocks recursive.
            # render_blocks expects 'BlockInstance' objects with .params and .definition_id
            
            blocks_payload = data.get('blocks', [])
            
            class MockBlock:
                def __init__(self, data):
                    self.id = data.get('id') or str(uuid.uuid4())
                    self.definition_id = data.get('type')
                    self.params = data.get('params', {})
                    self.placement_key = data.get('zone', 'main') # 'main', 'header', etc.
                    self.children_data = data.get('children', [])
                    # We don't strictly need .parent relation if we handle recursion manually, 
                    # but the generator uses BlockInstance.objects.filter(parent=block)
                    # We need to adapt the generator or the mock.
                    
                    # Optimization: The generator's `render_blocks` recursively fetches children via DB.
                    # We must intercept that.
            
            # PROBLEM: The existing `render_blocks` function inside `_generate_page_markdown` 
            # does: children = BlockInstance.objects.filter(parent=block)
            # This is hard-coded DB access.
            # We need to fix `_generate_page_markdown` recursively first.
            
            # For now, let's assume I fix `_generate_page_markdown` in the same edit 
            # to look at `block.cached_children` if available.
            
            def build_mock_block_tree(block_data_list):
                mocks = []
                for b_data in block_data_list:
                    mb = MockBlock(b_data)
                    # Recursively build children
                    if mb.children_data:
                        mb.cached_children = build_mock_block_tree(mb.children_data)
                    else:
                        mb.cached_children = []
                    mocks.append(mb)
                return mocks
            
            mock_blocks_tree = build_mock_block_tree(blocks_payload)
            
            # Filter for specific zones since `page_blocks` expected by generator is a QuerySet-like iterable
            # The generator filters by placement_key manually for zones.
            
            # We need a list that behaves sufficiently like the QuerySet for the initial loop
            # The initial loop in `_generate_page_markdown` does:
            # zone_blocks = page_blocks.filter(placement_key=zone_name)
            
            class MockQuerySet(list):
                def filter(self, **kwargs):
                    filtered = []
                    for item in self:
                        match = True
                        for k, v in kwargs.items():
                            if getattr(item, k, None) != v:
                                match = False
                                break
                        if match:
                            filtered.append(item)
                    return MockQuerySet(filtered)
                
                def order_by(self, *args):
                    return self # Assume already ordered from frontend
                
                def exists(self):
                    return len(self) > 0

            mock_page_blocks = MockQuerySet(mock_blocks_tree)
            
            # Get Global Blocks (Header/Footer) - Use Real DB blocks for now to save payload size
            # OR if payload includes them, use them.
            global_blocks_payload = data.get('global_blocks', [])
            if global_blocks_payload:
                 mock_global_blocks = MockQuerySet(build_mock_block_tree(global_blocks_payload))
            else:
                 mock_global_blocks = BlockInstance.objects.filter(page=None, parent=None, website=website).order_by('sort_order')

            
            # --- 2. Generate Markdown ---
            # Determine output path
            output_dir = Path(settings.BASE_DIR) / 'hugo_output' / website.slug
            content_dir = output_dir / 'content'
            content_dir.mkdir(parents=True, exist_ok=True)
            
            # We use a special filename for preview to minimize collision
            preview_filename = 'preview_canvas.md'
            # But wait, Hugo generates URLs based on filename/folder.
            # If we want the CSS paths to be correct, we should ideally use the real path?
            # Or content/_index.md for home.
            
            is_homepage = (mock_page.slug == '/' or mock_page.slug == '')
            if is_homepage:
                 page_file = content_dir / '_index.md'
            else:
                 # Clean slug
                 clean_slug = mock_page.slug.strip('/')
                 page_dir = content_dir / clean_slug
                 page_dir.mkdir(parents=True, exist_ok=True)
                 page_file = page_dir / 'index.md'

            # Generate URL base for assets
            # We want assets to point to /api/sites/{id}/preview/assets/...
            # helper string
            base_url = f"/api/sites/{website_id}/preview/" 

            markdown_content = self._generate_page_markdown(
                mock_page, 
                page_blocks=mock_page_blocks, 
                global_blocks=mock_global_blocks, 
                base_url=base_url
            )
            
            # Write to disk
            with open(page_file, 'w') as f:
                f.write(markdown_content)
                
            # --- 3. Run Hugo ---
            # Only build, don't deploy
            # We can use subprocess to run hugo in that dir
            
            # Use local hugo binary if available (same logic as HugoBuilder)
            hugo_binary = settings.BASE_DIR / 'bin' / 'hugo'
            if not hugo_binary.exists():
                hugo_binary = 'hugo' # Fallback to system path
            
            cmd = [str(hugo_binary), '-b', base_url]
            # Minify to ensure it's close to prod? Or maybe not, for debug. 
            # Let's keep it simple.
            
            result = subprocess.run(
                cmd, 
                cwd=output_dir, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print("Hugo Build Failed STDERR:", result.stderr)
                print("Hugo Build Failed STDOUT:", result.stdout)
                return Response({'error': 'Hugo build failed', 'details': result.stderr + "\n" + result.stdout}, status=500)
                
            # --- 4. Success ---
            # We no longer read HTML here. The client will fetch it via the src URL.
            
            return Response({
                'success': True,
                'logs': result.stdout
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

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
            flex_rendered = False  # Track if flex container was already rendered
            
            for zone in zones:
                zone_name = zone.get('name', 'main')
                zone_width = zone.get('width', 'flex-1')
                zone_css = zone.get('cssClasses', '')
                zone_order = zone.get('order', 0)
                
                if zone_width == 'w-full':
                    # Full-width zone (header/footer) with inner container for consistent width
                    if zone_name == 'header':
                        template_parts.append(f'    {{{{/* Header Zone */}}}}')
                        template_parts.append(f'    <header class="w-full {zone_css}">')
                        template_parts.append(f'        <div class="container mx-auto px-4 py-4 flex items-center justify-between">')
                        template_parts.append(f'        {{{{ range .Params.{zone_name}_blocks }}}}')
                        template_parts.append(f'            {{{{ partial "blocks/render-block.html" . }}}}')
                        template_parts.append(f'        {{{{ end }}}}')
                        template_parts.append(f'        </div>')
                        template_parts.append(f'    </header>')
                    elif zone_name == 'footer':
                        template_parts.append(f'    {{{{/* Footer Zone */}}}}')
                        template_parts.append(f'    <footer class="w-full mt-auto {zone_css}">')
                        template_parts.append(f'        <div class="container mx-auto px-4 py-8">')
                        template_parts.append(f'        {{{{ range .Params.{zone_name}_blocks }}}}')
                        template_parts.append(f'            {{{{ partial "blocks/render-block.html" . }}}}')
                        template_parts.append(f'        {{{{ end }}}}')
                        template_parts.append(f'        </div>')
                        template_parts.append(f'    </footer>')
                    else:
                        template_parts.append(f'    <div class="w-full {zone_css}">')
                        template_parts.append(f'        <div class="container mx-auto px-4 py-4">')
                        template_parts.append(f'        {{{{ range .Params.{zone_name}_blocks }}}}')
                        template_parts.append(f'            {{{{ partial "blocks/render-block.html" . }}}}')
                        template_parts.append(f'        {{{{ end }}}}')
                        template_parts.append(f'        </div>')
                        template_parts.append(f'    </div>')
                
                # Check if we need to start a flex container for non-full-width zones
                elif not flex_rendered and zone_order > current_order and any(z.get('order', 0) > current_order and z.get('width') != 'w-full' for z in zones):
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
                    flex_rendered = True  # Mark flex as done, continue to render footer
            
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
        if hasattr(page, 'website'):
            global_blocks = BlockInstance.objects.filter(page=None, parent=None, website=page.website).order_by('sort_order')
        else:
            # Mock page might not have website relation set up for DB query
            global_blocks = [] # Should be passed in if needed, but for now fallback

    def _generate_page_markdown(self, page, page_blocks=None, global_blocks=None, base_url=""):
        """
        Generate markdown file content for a page including frontmatter and blocks.
        If page_blocks/global_blocks are provided, uses those instead of DB queries.
        """
        # Get blocks for this page (page-specific blocks in main/sidebar zones)
        if page_blocks is None:
            page_blocks = BlockInstance.objects.filter(page=page, parent=None).order_by('sort_order')
        
        # Get global blocks (header/footer blocks with page=None)
        if global_blocks is None:
            global_blocks = BlockInstance.objects.filter(page=None, parent=None, website=page.website).order_by('sort_order')
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
                # --- Transform flex_columns to row + column with proper params ---
                if block.definition_id == 'flex_columns':
                    # Get column widths
                    col_widths_str = block.params.get('col_widths', '50.0, 50.0')
                    col_widths = [w.strip() for w in col_widths_str.split(',')]
                    
                    # Get children grouped by placement_key
                    # Get children grouped by placement_key
                    if hasattr(block, 'cached_children'):
                        # Support for mock blocks that pre-fetch children
                        qs = block.cached_children
                        if isinstance(qs, list):
                             class MockQS(list):
                                 def order_by(self, *args): return self
                                 def filter(self, **kwargs):
                                      res = []
                                      for item in self:
                                          match = True
                                          for k, v in kwargs.items():
                                              val = getattr(item, k, None)
                                              if val != v:
                                                  match = False
                                                  # Handle simple startswith logic if needed, but strict eq is usually enough for mock
                                                  if k == 'placement_key__startswith' and val and val.startswith(v):
                                                      match = True # crude fix for complex lookups if they appear
                                                  else:
                                                      break
                                          if match:
                                              res.append(item)
                                      return MockQS(res)
                                 def exists(self): return len(self) > 0
                             fc_children = MockQS(qs)
                        else:
                             fc_children = qs
                    else:
                        fc_children = BlockInstance.objects.filter(parent=block).order_by('sort_order')
                    
                    # Check if children use legacy col_N keys
                    has_legacy_keys = any(child.placement_key and child.placement_key.startswith('col_') for child in fc_children)
                    
                    output += f"{indent}[[{zone_name}]]\n"
                    # Treat flex_columns as a row with flex_mode=true
                    output += f'{indent}  type = "row"\n'
                    output += f'{indent}  flex_mode = true\n'
                    output += f'{indent}  gap = "2"\n'
                    if block.params.get('css_classes'):
                        css = str(block.params['css_classes']).replace('\\', '\\\\').replace('"', '\\"')
                        output += f'{indent}  css_classes = "{css}"\n'
                    
                    if not has_legacy_keys and fc_children.exists():
                        # NEW FORMAT: Children are likely 'column' blocks (or sequential content)
                        # We just render them as children of the row.
                        # If they are 'column' type, they will be rendered as columns.
                        output += render_blocks(fc_children, f"{zone_name}.blocks", depth + 1)
                    
                    else:
                        # LEGACY FORMAT: Children are mapped to col_N
                        children_by_col = {}
                        for child in fc_children:
                            col_key = child.placement_key or 'col_0'
                            if col_key not in children_by_col:
                                children_by_col[col_key] = []
                            children_by_col[col_key].append(child)
                            
                        # Output each column with width_percent
                        for col_index, width in enumerate(col_widths):
                            col_key = f'col_{col_index}'
                            # Only generate a column wrapper if we are in Legacy mode AND converting content to columns
                            # For Legacy, the children were CONTENT, so we wrap them in a Column block.
                            output += f"{indent}  [[{zone_name}.blocks]]\n"
                            output += f'{indent}    type = "column"\n'
                            output += f'{indent}    width_percent = "{width}"\n'
                            
                            # Recursively render column's children
                            col_children = children_by_col.get(col_key, [])
                            if col_children:
                                output += render_blocks(col_children, f"{zone_name}.blocks.blocks", depth + 2)
                    
                    continue  # Skip default handling

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
                    # Support both 'features' and 'items' keys, output as 'features' for template
                    features = params.get('features', params.get('items', []))
                    if features:
                        features_toml = "["
                        for i, item in enumerate(features):
                            if i > 0:
                                features_toml += ", "
                            icon = str(item.get("icon", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            title = str(item.get("title", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            description = str(item.get("description", "")).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                            features_toml += f'{{icon = "{icon}", title = "{title}", description = "{description}"}}'
                        features_toml += "]\n"
                        output += f'{indent}  features = {features_toml}'
                
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
                
                # Handle carousel-specific parameters (slides are stored as JSON, not BlockInstance children)
                # NOTE: Carousels MUST use 'params.slides' as defined in the BlockDefinition schema (see migration 0031).
                # Do NOT use 'children' (BlockInstance.children) for carousel slides, as the Editor expects 'slides' property.
                if block.definition_id == 'carousel':
                    slides = params.get('slides', [])
                    if slides:
                        # Flatten slides into a blocks array for the template
                        # Each slide's children become direct blocks in the carousel
                        all_slide_blocks = []
                        for slide in slides:
                            for child in slide.get('children', []):
                                all_slide_blocks.append(child)
                        
                        if all_slide_blocks:
                            # Output each child block as [[zone.blocks]]
                            for child_block in all_slide_blocks:
                                child_type = child_block.get('type', 'unknown')
                                child_params = child_block.get('params', {})
                                output += f'{indent}  [[{zone_name}.blocks]]\n'
                                output += f'{indent}    type = "{child_type}"\n'
                                
                                # Serialize child params
                                for k, v in child_params.items():
                                    if k == 'type':
                                        continue
                                    if isinstance(v, bool):
                                        v_toml = "true" if v else "false"
                                        output += f'{indent}    {k} = {v_toml}\n'
                                    elif isinstance(v, (int, float)):
                                        output += f'{indent}    {k} = {v}\n'
                                    elif isinstance(v, list):
                                        # Handle arrays (like reviews in google_reviews)
                                        if v and isinstance(v[0], dict):
                                            arr_toml = "["
                                            for i, item in enumerate(v):
                                                if i > 0:
                                                    arr_toml += ", "
                                                item_str = "{"
                                                item_parts = []
                                                for ik, iv in item.items():
                                                    iv_str = str(iv).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                                                    item_parts.append(f'{ik} = "{iv_str}"')
                                                item_str += ", ".join(item_parts)
                                                item_str += "}"
                                                arr_toml += item_str
                                            arr_toml += "]"
                                            output += f'{indent}    {k} = {arr_toml}\n'
                                    elif not isinstance(v, dict):
                                        v_str = str(v).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                                        output += f'{indent}    {k} = "{v_str}"\n'
                
                
                
                # --- Recursive Child Rendering ---
                # Check for children (nested blocks)
                # MOD: Support cached_children (from mock) or DB query
                if hasattr(block, 'cached_children'):
                    children = block.cached_children
                    start_children = True # It's a list, effectively exists if not empty
                else:
                    children = BlockInstance.objects.filter(parent=block).order_by('sort_order')
                    start_children = children.exists()

                if start_children:
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
        full_markdown = frontmatter + content + "+++\n"
        print("DEBUG: Generated Markdown:\n" + full_markdown[:2000] + "...") # Log first 2000 chars
        return full_markdown
    
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
            # Don't auto-select a website - let the frontend show empty state
            current_website = None
            
        # Only fetch global blocks if we have a current website
        header_blocks = []
        footer_blocks = []
        if current_website:
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
    queryset = Page.objects.all().order_by('sort_order', '-updated_at')
    
    def get_queryset(self):
        queryset = Page.objects.all().order_by('sort_order', '-updated_at')
        website_id = self.request.query_params.get('website_id')
        
        if website_id:
            queryset = queryset.filter(website_id=website_id)
        elif self.action == 'list':
            # Only restrict list view if no website_id is provided
            # Detail views (retrieve, content, etc) work by ID so we don't strictly need website_id
            return Page.objects.none()
            
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

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder pages based on a list of {id, sort_order}.
        """
        page_orders = request.data.get('pages', [])
        if not page_orders:
            return Response({'error': 'No pages provided'}, status=400)
            
        try:
            with transaction.atomic():
                for item in page_orders:
                    page_id = item.get('id')
                    sort_order = item.get('sort_order')
                    if page_id is not None and sort_order is not None:
                        Page.objects.filter(id=page_id).update(sort_order=sort_order)
            return Response({'status': 'success'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

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

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """
        Clones a page and all its blocks.
        """
        original_page = self.get_object()
        
        try:
            with transaction.atomic():
                # 1. Clone Page
                new_page = Page.objects.get(pk=original_page.pk)
                new_page.pk = None
                new_page.title = f"{original_page.title} (copy)"
                new_page.status = 'draft'
                new_page.last_published_at = None
                
                # Handle slug uniqueness
                base_slug = f"{original_page.slug}-copy"
                new_slug = base_slug
                counter = 1
                while Page.objects.filter(website=original_page.website, slug=new_slug).exists():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                new_page.slug = new_slug
                new_page.save()
                
                # 2. Clone Blocks (Recursive)
                def clone_block_recursive(original_block, parent_block=None):
                    # Get fresh copy of the block data
                    new_block = BlockInstance.objects.get(pk=original_block.pk)
                    new_block.pk = None # Reset ID to create new instance
                    new_block.page = new_page
                    new_block.parent = parent_block
                    new_block.save()
                    
                    # Clone children
                    children = BlockInstance.objects.filter(parent=original_block).order_by('sort_order')
                    for child in children:
                        clone_block_recursive(child, parent_block=new_block)

                # Clone top-level blocks
                top_level_blocks = BlockInstance.objects.filter(page=original_page, parent=None).order_by('sort_order')
                for block in top_level_blocks:
                    clone_block_recursive(block)
                    
                serializer = PageDetailSerializer(new_page)
                return Response(serializer.data)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

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
                template_slug=serializer.validated_data['template_slug'],
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                tags=serializer.validated_data.get('tags', []),
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
                template_slug=template.slug,
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
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlockTemplateViewSet(viewsets.ViewSet):
    """
    Serves the raw Handlebars templates to the frontend.
    """
    def list(self, request):
        templates_dir = Path(settings.BASE_DIR) / 'hugo' / 'templates' / 'blocks'
        templates = {}
        
        if templates_dir.exists():
            for hbs_file in templates_dir.glob('*.hbs'):
                try:
                    templates[hbs_file.stem] = hbs_file.read_text(encoding='utf-8')
                except Exception as e:
                    print(f"Error reading block template {hbs_file}: {e}")
                    
        return Response(templates)
