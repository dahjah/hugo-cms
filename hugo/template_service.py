"""
Template service for exporting websites to templates and creating websites from templates.
"""
from django.db import transaction
from .models import (
    Website, Page, BlockInstance, BlockDefinition,
    SiteTemplate, TemplateCategory
)
import uuid


def serialize_blocks_for_template(blocks):
    """
    Recursively serialize blocks for template storage.
    Returns a list of block dicts that can be deserialized later.
    """
    result = []
    for block in blocks:
        block_data = {
            'type': block.definition.id,
            'params': block.params,
            'placement_key': block.placement_key,
            'sort_order': block.sort_order,
            'children': []
        }
        # Recursively serialize children
        children = block.children.all().order_by('sort_order')
        if children.exists():
            block_data['children'] = serialize_blocks_for_template(children)
        result.append(block_data)
    return result


def deserialize_blocks_from_template(blocks_data, page, parent=None, website=None):
    """
    Recursively create BlockInstance objects from serialized template data.
    """
    for block_data in blocks_data:
        try:
            definition = BlockDefinition.objects.get(id=block_data['type'])
        except BlockDefinition.DoesNotExist:
            # Skip blocks with missing definitions
            continue
        
        block = BlockInstance.objects.create(
            definition=definition,
            page=page if parent is None else None,
            parent=parent,
            website=website,
            placement_key=block_data['placement_key'],
            sort_order=block_data['sort_order'],
            params=block_data.get('params', {})
        )
        
        # Recursively create children
        children_data = block_data.get('children', [])
        if children_data:
            deserialize_blocks_from_template(children_data, page, parent=block, website=website)


def export_website_to_template(website_id, template_id, name, description='', category_slug=None, thumbnail_url='', created_by=''):
    """
    Export a website's pages, blocks, and CSS to a SiteTemplate.
    
    Args:
        website_id: UUID of the website to export
        template_id: String ID for the new template (e.g., 'therapy')
        name: Display name for the template
        description: Optional description
        category_slug: Optional category slug
        thumbnail_url: Optional preview image URL
        created_by: Optional attribution
    
    Returns:
        SiteTemplate instance
    """
    website = Website.objects.get(id=website_id)
    pages = Page.objects.filter(website=website)
    
    pages_json = []
    for page in pages:
        # Get top-level blocks for this page (blocks with page=page and parent=None)
        main_blocks = BlockInstance.objects.filter(
            page=page, 
            parent=None
        ).order_by('placement_key', 'sort_order')
        
        page_data = {
            'slug': page.slug,
            'title': page.title,
            'layout': page.layout,
            'description': page.description,
            'blocks': serialize_blocks_for_template(main_blocks)
        }
        pages_json.append(page_data)
    
    # Also capture global header/footer blocks (blocks with website=website, page=None, parent=None)
    global_blocks = BlockInstance.objects.filter(
        website=website,
        page=None,
        parent=None
    ).order_by('placement_key', 'sort_order')
    
    global_blocks_json = serialize_blocks_for_template(global_blocks)
    
    # Get category if provided
    category = None
    if category_slug:
        try:
            category = TemplateCategory.objects.get(slug=category_slug)
        except TemplateCategory.DoesNotExist:
            pass
    
    # Create or update the template
    template, created = SiteTemplate.objects.update_or_create(
        id=template_id,
        defaults={
            'name': name,
            'description': description,
            'thumbnail_url': thumbnail_url,
            'category': category,
            'base_css': website.custom_css or '',
            'pages_json': {
                'pages': pages_json,
                'global_blocks': global_blocks_json
            },
            'created_by': created_by,
        }
    )
    
    return template


@transaction.atomic
def create_website_from_template(template_id, website_name, website_slug):
    """
    Create a new website with pages and blocks from a template.
    
    Args:
        template_id: ID of the template to use
        website_name: Name for the new website
        website_slug: URL slug for the new website
    
    Returns:
        Website instance
    """
    template = SiteTemplate.objects.get(id=template_id)
    
    # Create the website
    website = Website.objects.create(
        name=website_name,
        slug=website_slug,
        custom_css=template.base_css
    )
    
    template_data = template.pages_json
    pages_data = template_data.get('pages', []) if isinstance(template_data, dict) else template_data
    global_blocks_data = template_data.get('global_blocks', []) if isinstance(template_data, dict) else []
    
    # Create pages and blocks
    for page_data in pages_data:
        page = Page.objects.create(
            website=website,
            slug=page_data['slug'],
            title=page_data['title'],
            layout=page_data.get('layout', 'single'),
            description=page_data.get('description', ''),
            status='draft'
        )
        
        # Create blocks for this page
        blocks_data = page_data.get('blocks', [])
        deserialize_blocks_from_template(blocks_data, page, parent=None, website=website)
    
    # Create global blocks (header/footer)
    for block_data in global_blocks_data:
        deserialize_blocks_from_template([block_data], None, parent=None, website=website)
    
    return website
