"""
Hugo Site Importer - Import external Hugo sites into Hugo CMS.

Parses Hugo content/*.md files, data/*.yaml files, and assets to create 
CMS Website, Pages, and BlockInstances.

This importer handles:
1. Frontmatter (title, description, layout)
2. Shortcodes (hero, section, two-col, testimonials, specialties, modalities)  
3. Raw HTML content between shortcodes
4. Nested shortcode structures
5. Data-driven shortcodes that load from data/*.yaml files
"""
import os
import re
import yaml
from pathlib import Path
from django.db import transaction
from .models import (
    Website, Page, BlockInstance, BlockDefinition
)
import shutil
from django.conf import settings


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from a markdown file.
    Returns (frontmatter_dict, body_content).
    """
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return frontmatter, body
    return {}, content


def load_data_files(hugo_root):
    """
    Load all YAML/JSON data files from the data/ directory.
    Returns dict: {'testimonials': [...], 'specialties': [...], ...}
    """
    data_dir = Path(hugo_root) / 'data'
    data = {}
    
    if not data_dir.exists():
        return data
    
    for file_path in data_dir.glob('*.yaml'):
        key = file_path.stem
        with open(file_path, 'r') as f:
            data[key] = yaml.safe_load(f) or []
    
    for file_path in data_dir.glob('*.yml'):
        key = file_path.stem
        with open(file_path, 'r') as f:
            data[key] = yaml.safe_load(f) or []
    
    return data


def load_css(hugo_root):
    """
    Load CSS from assets/css/main.css if it exists.
    """
    css_paths = [
        Path(hugo_root) / 'assets' / 'css' / 'main.css',
        Path(hugo_root) / 'static' / 'css' / 'style.css',
        Path(hugo_root) / 'assets' / 'css' / 'style.css',
    ]
    
    for css_path in css_paths:
        if css_path.exists():
            with open(css_path, 'r') as f:
                return f.read()
    
    return ''


def extract_inner_html(content):
    """
    Remove all Hugo shortcode tags from content, keeping only the HTML/text between them.
    """
    # Remove shortcode tags but keep content between them
    # First remove self-closing shortcodes
    content = re.sub(r'\{\{[<\%]\s*[\w-]+[^>]*?/?\s*[>\%]\}\}', '', content)
    # Remove opening shortcode tags
    content = re.sub(r'\{\{[<\%]\s*[\w-]+[^>]*?\s*[>\%]\}\}', '', content)
    # Remove closing shortcode tags
    content = re.sub(r'\{\{[<\%]\s*/[\w-]+\s*[>\%]\}\}', '', content)
    
    return content.strip()


def split_into_content_blocks(body, data_files, container_tags=None):
    """
    Recursively split the body into a tree of content blocks.
    container_tags: list of shortcode names that should be treated as containers.
    """
    if container_tags is None:
        container_tags = ['section', 'row', 'column', 'two-col', 'col']

    blocks = []
    
    # Regex to find shortcodes: {{< name params >}} or {{% name params %}}
    # We capture the full tag, the type (< or %), the name, and params
    tag_pattern = re.compile(r'(\{\{([<%])\s*([/\w-]+)(.*?)([>%])\}\})', re.DOTALL)
    
    cursor = 0
    while cursor < len(body):
        match = tag_pattern.search(body, cursor)
        if not match:
            # No more tags, add remaining text as HTML
            remaining = body[cursor:].strip()
            if remaining:
                blocks.append({
                    'type': 'html',
                    'name': 'html',
                    'params': {},
                    'content': remaining
                })
            break
        
        # Add text before the tag as HTML
        pre_text = body[cursor:match.start()].strip()
        if pre_text:
            blocks.append({
                'type': 'html',
                'name': 'html',
                'params': {},
                'content': pre_text
            })
            
        # Process the tag
        full_tag = match.group(1)
        tag_type = match.group(2) # < or %
        tag_name = match.group(3).strip()
        tag_params_str = match.group(4).strip()
        is_closing = tag_name.startswith('/')
        clean_name = tag_name.lstrip('/')
        
        if is_closing:
            # Should be handled by the recursion caller, but if we see it here, 
            # it might be an orphan or we are at top level.
            # For now, treat as text or skip.
            cursor = match.end()
            continue
            
        # Parse params
        params = {}
        # Simple param parser: key="value" or key='value' or just value
        param_matches = re.finditer(r'(\w+)=["\']([^"\']*)["\']|(\w+)=([^ \t\n]+)', tag_params_str)
        for pm in param_matches:
            if pm.group(1):
                params[pm.group(1)] = pm.group(2)
            elif pm.group(3):
                params[pm.group(3)] = pm.group(4)
        
        # Check if it's a container block
        if clean_name in container_tags:
            # Container block - find matching closing tag
            # We need to scan forward counting nesting level
            nesting = 1
            search_pos = match.end()
            content_end = -1
            
            while True:
                next_match = tag_pattern.search(body, search_pos)
                if not next_match:
                    break
                
                next_name = next_match.group(3).strip().lstrip('/')
                next_is_closing = next_match.group(3).strip().startswith('/')
                
                if next_name == clean_name:
                    if next_is_closing:
                        nesting -= 1
                        if nesting == 0:
                            content_end = next_match.start()
                            cursor = next_match.end()
                            break
                    else:
                        nesting += 1
                
                search_pos = next_match.end()
            
            if content_end != -1:
                # Found closing tag
                inner_content = body[match.end():content_end]
                # Recursively parse children
                children = split_into_content_blocks(inner_content, data_files, container_tags)
                blocks.append({
                    'type': 'shortcode',
                    'name': clean_name,
                    'params': params,
                    'children': children
                })
            else:
                # No closing tag found, treat as self-closing or error
                # Just add as empty container
                blocks.append({
                    'type': 'shortcode',
                    'name': clean_name,
                    'params': params,
                    'children': []
                })
                cursor = match.end()
        else:
            # Treat as self-closing/void block if not a container
            blocks.append({
                'type': 'shortcode',
                'name': clean_name,
                'params': params,
                'children': []
            })
            cursor = match.end()
            
    return blocks


def convert_content_blocks_to_cms_blocks(content_blocks, data_files, website, media_url_base='/'):
    """
    Convert parsed content blocks to CMS BlockInstance param dicts.
    """
    cms_blocks = []
    
    for block in content_blocks:
        block_type = block['type']
        name = block['name']
        params = block['params']
        children_data = block.get('children', [])
        
        definition_id = None
        block_params = {}
        
        if block_type == 'html':
            definition_id = 'html'
            block_params = {'content': block['content']}
            
        elif block_type == 'shortcode':
            if name == 'hero':
                definition_id = 'hero'
                # Fix image path
                image_path = params.get('image', '')
                if image_path.startswith('/'):
                    image_path = f"{media_url_base}{image_path.lstrip('/')}"
                block_params = {
                    'title': params.get('title', ''),
                    'subtitle': params.get('subtitle', ''),
                    'bgImage': image_path
                }
                
            elif name == 'testimonials':
                definition_id = 'carousel'
                block_params = {
                    'auto_advance': True,
                    'interval_seconds': 8,
                    'show_dots': True,
                    'show_arrows': True
                }
                
                # Create child testimonial blocks
                testimonials = data_files.get('testimonials', [])
                testimonial_children = []
                try:
                    testimonial_def = BlockDefinition.objects.get(id='testimonial')
                    for i, t in enumerate(testimonials):
                        testimonial_children.append({
                            'definition': testimonial_def,
                            'params': {
                                'quote': t.get('quote', ''),
                                'author': t.get('author', '')
                            },
                            'children': [],
                            'placement_key': 'slide', # Link to carousel parent
                            'sort_order': i
                        })
                except BlockDefinition.DoesNotExist:
                    print("DEBUG: BlockDefinition 'testimonial' NOT FOUND")
                    pass
                
                # We need to expose these children to the recursive creator.
                # Since the standard flow uses `children_data` (parsed from nested tags),
                # and here we are synthesizing children from data, we'll assign to `cms_children` below.
                pass 

            elif name == 'section':
                definition_id = 'section'
                block_params = {'style': params.get('style', 'default')}
                
            elif name == 'two-col':
                definition_id = 'row'
                block_params = {
                    'ratio': params.get('ratio', ''), # Pass ratio through to be handled in recursion
                    'reverse': params.get('reverse', 'false'),
                    'class': params.get('class', '')
                }
                
            elif name == 'col':
                definition_id = 'column'
                block_params = {
                    'span': '1',
                    'class': params.get('class', '')
                }
                
            elif name == 'specialties':
                definition_id = 'flip_cards'
                specialties = data_files.get('specialties', [])
                cards = []
                for s in specialties:
                    cards.append({
                        'front': {'title': s.get('title', ''), 'icon': ''},
                        'back': {'description': s.get('description', ''), 'action': 'Learn More'}
                    })
                block_params = {'cards': cards, 'columns': 3}
                
            elif name == 'modalities':
                definition_id = 'accordion'
                modalities = data_files.get('modalities', [])
                items = []
                for m in modalities:
                    items.append({
                        'title': m.get('name', m.get('title', '')), 
                        'content': m.get('description', '')
                    })
                block_params = {'items': items, 'allow_multiple': False}

            # Fallback for generic blocks (e.g. row, column, section if not handled above)
            if not definition_id:
                try:
                    # Check if a block definition exists with this name
                    # Note: params are passed as-is, assuming they match the schema
                    BlockDefinition.objects.get(id=name)
                    definition_id = name
                    block_params = params
                except BlockDefinition.DoesNotExist:
                    pass
        
        if definition_id:
            try:
                definition = BlockDefinition.objects.get(id=definition_id)
                
                if definition_id == 'testimonials':
                     cms_children = children_data
                else:
                    # Recursively convert children
                    cms_children = convert_content_blocks_to_cms_blocks(children_data, data_files, website, media_url_base)
                
                # Handle special children for testimonials
                if name == 'testimonials':
                    cms_children = [] # Reset any parsed children (should be none)
                    testimonials = data_files.get('testimonials', [])
                    try:
                        testimonial_def = BlockDefinition.objects.get(id='testimonial')
                        for i, t in enumerate(testimonials):
                            cms_children.append({
                                'definition': testimonial_def,
                                'params': {
                                    'quote': t.get('quote', ''),
                                    'author': t.get('author', '')
                                },
                                'children': [],
                                'placement_key': 'slide',
                                'sort_order': i
                            })
                    except BlockDefinition.DoesNotExist:
                        pass

                # If we synthesized children (e.g. for testimonials), allow appending them
                if name == 'testimonials' and 'testimonial_children' in locals():
                     cms_children.extend(testimonial_children)

                cms_blocks.append({
                    'definition': definition,
                    'params': block_params,
                    'children': cms_children
                })
            except BlockDefinition.DoesNotExist:
                pass
    
    return cms_blocks


    return cms_blocks


def copy_assets(hugo_root, website_slug):
    """
    Copy static assets (images, etc.) from Hugo site to CMS media directory.
    """
    # Source directories
    static_dir = Path(hugo_root) / 'static'
    assets_dir = Path(hugo_root) / 'assets'
    
    # Target directory: media/uploads/{website_slug}/
    target_dir = Path(settings.MEDIA_ROOT) / 'uploads' / website_slug
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy static files
    if static_dir.exists():
        for item in static_dir.glob('**/*'):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(static_dir)
                dest = target_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
    
    # Copy assets (images only)
    if assets_dir.exists():
        for item in assets_dir.glob('**/*'):
            if item.is_file() and item.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                rel_path = item.relative_to(assets_dir)
                dest = target_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    return f"/media/uploads/{website_slug}/"


@transaction.atomic
def import_hugo_site(hugo_root, website_name, website_slug):
    """
    Import an external Hugo site into Hugo CMS.
    
    Args:
        hugo_root: Path to the Hugo site root directory
        website_name: Name for the new CMS website
        website_slug: URL slug for the new website
    
    Returns:
        Website instance
    """
    hugo_path = Path(hugo_root)
    
    if not hugo_path.exists():
        raise ValueError(f"Hugo site path does not exist: {hugo_root}")
    
    # Load data files
    data_files = load_data_files(hugo_root)
    
    # Load CSS
    custom_css = load_css(hugo_root)
    
    # Create website
    website = Website.objects.create(
        name=website_name,
        slug=website_slug,
        custom_css=custom_css
    )
    
    # Copy assets
    media_url_base = copy_assets(hugo_root, website_slug)
    
    # Parse content files
    content_dir = hugo_path / 'content'
    if not content_dir.exists():
        return website
    
    # Find all markdown files
    md_files = list(content_dir.glob('**/*.md'))
    
    for md_file in md_files:
        # Determine page slug from file path
        relative_path = md_file.relative_to(content_dir)
        
        if md_file.name == '_index.md':
            # Homepage or section index
            if md_file.parent == content_dir:
                slug = '/'
            else:
                slug = '/' + str(relative_path.parent)
        elif md_file.name == 'index.md':
            # Page bundle
            slug = '/' + str(relative_path.parent)
        else:
            # Regular page
            slug = '/' + str(relative_path.with_suffix(''))
        
        # Read and parse content
        with open(md_file, 'r') as f:
            content = f.read()
        
        frontmatter, body = parse_frontmatter(content)
        
        # Create page
        page = Page.objects.create(
            website=website,
            title=frontmatter.get('title', md_file.stem.replace('-', ' ').title()),
            slug=slug,
            layout=frontmatter.get('layout', 'single'),
            description=frontmatter.get('description', ''),
            status='draft'
        )
        
        # Get list of container blocks from DB
        container_blocks = list(BlockDefinition.objects.filter(is_container=True).values_list('id', flat=True))
        # Add legacy container tags
        container_tags = set(container_blocks) | {'two-col', 'col', 'section'}
        
        # Parse body content
        content_blocks = split_into_content_blocks(body, data_files, list(container_tags))
        
        # Convert to CMS blocks
        cms_blocks = convert_content_blocks_to_cms_blocks(content_blocks, data_files, website, media_url_base)
        
        # Create block instances
        def create_blocks_recursive(blocks_data, parent=None, page=None, placement_key='main'):
            for i, block_data in enumerate(blocks_data):
                # Determine placement key
                # If parent is two_col, children are cols. 
                # If parent is col, children are content.
                # We can just use 'child' or 'block' as generic key, or inherit.
                # For carousel, we used 'slide'.
                
                pk = block_data.get('placement_key', placement_key)
                if parent and parent.definition.id == 'carousel':
                    pk = 'slide'
                elif parent and parent.definition.id == 'row':
                    pk = 'column'
                
                # Handle row ratio logic
                if block_data['definition'].id == 'row':
                    ratio = block_data['params'].get('ratio', '') # e.g. "60-40"
                    if ratio:
                        parts = ratio.split('-')
                        children = block_data.get('children', [])
                        for idx, child in enumerate(children):
                            if idx < len(parts) and child['definition'].id == 'column':
                                child['params']['width'] = f"{parts[idx]}%"

                instance = BlockInstance.objects.create(
                    definition=block_data['definition'],
                    page=page if parent is None else None,
                    website=website,
                    parent=parent,
                    placement_key=pk,
                    sort_order=block_data.get('sort_order', i),
                    params=block_data['params']
                )
                
                # Create children
                children = block_data.get('children', [])
                if children:
                    create_blocks_recursive(children, parent=instance, page=None, placement_key='blocks')

        create_blocks_recursive(cms_blocks, page=page)
    
    return website
