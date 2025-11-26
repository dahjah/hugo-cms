from django.db import models
from django.db.models import JSONField
from django.core.serializers.json import DjangoJSONEncoder
import uuid
import toml
from datetime import date
from django.db import transaction
from .models import Page, BlockDefinition, BlockInstance, LayoutTemplate

# --- MOCK HUGO ENVIRONMENT ---

MOCK_THEME_ARCHETYPE = {
    'title': 'New Page Title',
    'layout': 'default',
    'date': date.today().isoformat(),
    'description': 'Default description.',
    'tags': ['default'],
    # Mocking a theme that uses standard top-level component parameters
    'hero_title': 'Theme Landing Hero',
    'hero_subtitle': 'Easily editable content.',
    'feature_list': [
        {'icon': 'settings', 'text': 'Fully configurable.'},
        {'icon': 'code', 'text': 'Fast and modern.'},
    ]
}

def import_hugo_theme_structure(theme_name="mock-theme"):
    """
    Simulates importing a Hugo theme by translating its archetype/layout variables
    into CMS BlockDefinitions and creating an example Page.
    """
    
    # 1. Clear existing definitions and pages to start fresh (optional for dev)
    BlockDefinition.objects.all().delete()
    Page.objects.all().delete()
    BlockInstance.objects.all().delete()
    LayoutTemplate.objects.all().delete()

    # 2. CREATE DEFAULT LAYOUT TEMPLATES
    LayoutTemplate.objects.create(
        id='home',
        label='Home Page',
        zones=[
            {'name': 'header', 'width': 'w-full', 'order': 0, 'cssClasses': 'bg-slate-50/50'},
            {'name': 'main', 'width': 'flex-1', 'order': 1, 'cssClasses': 'min-h-[400px]'},
            {'name': 'footer', 'width': 'w-full', 'order': 2, 'cssClasses': 'bg-slate-50/50'},
        ],
        description='Standard layout with header, main content, and footer'
    )
    LayoutTemplate.objects.create(
        id='single',
        label='Standard Page',
        zones=[
            {'name': 'header', 'width': 'w-full', 'order': 0, 'cssClasses': 'bg-slate-50/50'},
            {'name': 'main', 'width': 'flex-1', 'order': 1, 'cssClasses': 'min-h-[400px]'},
            {'name': 'footer', 'width': 'w-full', 'order': 2, 'cssClasses': 'bg-slate-50/50'},
        ],
        description='Standard layout for single pages'
    )
    LayoutTemplate.objects.create(
        id='list',
        label='Sidebar Layout (Left)',
        zones=[
            {'name': 'header', 'width': 'w-full', 'order': 0, 'cssClasses': 'bg-slate-50/50'},
            {'name': 'sidebar', 'width': 'w-64', 'order': 1, 'cssClasses': 'border-r border-slate-100 bg-slate-50/30'},
            {'name': 'main', 'width': 'flex-1', 'order': 2, 'cssClasses': 'min-h-[400px]'},
            {'name': 'footer', 'width': 'w-full', 'order': 3, 'cssClasses': 'bg-slate-50/50'},
        ],
        description='Layout with sidebar on the left for list pages'
    )
    LayoutTemplate.objects.create(
        id='contact',
        label='Minimal / Contact',
        zones=[
            {'name': 'header', 'width': 'w-full', 'order': 0, 'cssClasses': 'bg-slate-50/50'},
            {'name': 'main', 'width': 'flex-1', 'order': 1, 'cssClasses': 'min-h-[400px]'},
        ],
        description='Minimal layout without footer'
    )

    definitions_map = {}
    
    # 2. INFER BASE DEFINITIONS
    inferred_definitions_data = []
    
    inferred_definitions_data.extend([
        {'id': 'hero', 'label': 'Hero Section', 'icon': 'layout', 'has_visual_preview': True, 'default_params': {'title': 'Welcome Home', 'subtitle': 'Start your journey here', 'bgImage': 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200&q=80'}},
        {'id': 'text', 'label': 'Text Block', 'icon': 'type', 'has_visual_preview': True, 'default_params': {'content': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'}},
        {'id': 'image', 'label': 'Image', 'icon': 'image', 'has_visual_preview': True, 'default_params': {'src': 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800&q=80', 'caption': 'A beautiful view'}},
        {'id': 'flex_columns', 'label': 'Flexible Columns', 'icon': 'columns', 'has_visual_preview': True, 'default_params': {'col_widths': '50.0, 50.0'}},
        {'id': 'markdown', 'label': 'Markdown', 'icon': 'file-text', 'has_visual_preview': True, 'default_params': {'md': '## Hello World\nThis is **markdown** content.'}},
        {'id': 'youtube', 'label': 'YouTube Embed', 'icon': 'video', 'has_visual_preview': False, 'default_params': {'videoId': 'dQw4w9WgXcQ', 'title': 'My Video'}},
        {'id': 'alert', 'label': 'Alert Box', 'icon': 'alert-triangle', 'has_visual_preview': False, 'default_params': {'type': 'warning', 'message': 'This is an important alert message.'}},
        {'id': 'quote', 'label': 'Blockquote', 'icon': 'type', 'has_visual_preview': False, 'default_params': {'text': 'Design is intelligence made visible.', 'author': 'Alina Wheeler'}},
        # Imported theme blocks
        {'id': 'theme_hero', 'label': f'{theme_name.capitalize()} Hero', 'icon': 'layout', 'has_visual_preview': False, 
            'default_params': {'title': MOCK_THEME_ARCHETYPE.get('hero_title', 'New Hero'), 'subtitle': MOCK_THEME_ARCHETYPE.get('hero_subtitle', 'Sub Title'), 'background_url': 'https://placehold.co/1200x500/1e293b/ffffff?text=Theme+Background'}},
        {'id': 'theme_features', 'label': f'{theme_name.capitalize()} Features', 'icon': 'columns', 'has_visual_preview': False,
            'default_params': {'title': 'Key Features', 'items': [{'icon': 'box', 'text': 'Item 1'}, {'icon': 'box', 'text': 'Item 2'}]}}
    ])
        
    # 3. Save Inferred Definitions
    for data in inferred_definitions_data:
        definition = BlockDefinition.objects.create(
            id=data['id'],
            label=data['label'],
            icon=data['icon'],
            has_visual_preview=data['has_visual_preview'],
            default_params=data['default_params']
        )
        definitions_map[data['id']] = definition

    # 4. CREATE EXAMPLE PAGE & CONTENT
    
    with transaction.atomic():
        example_page = Page.objects.create(
            id=uuid.uuid4(),
            title=f"{theme_name.capitalize()} Home",
            slug='/',
            status='draft',
            layout=MOCK_THEME_ARCHETYPE['layout'],
            description=MOCK_THEME_ARCHETYPE['description'],
            tags=MOCK_THEME_ARCHETYPE['tags'],
            date=MOCK_THEME_ARCHETYPE['date']
        )

        # 4a. Theme Hero Block (Top Level)
        if 'theme_hero' in definitions_map:
            hero_block = BlockInstance.objects.create(
                definition=definitions_map['theme_hero'],
                page=example_page,
                parent=None,
                placement_key='main',
                sort_order=0,
                params=definitions_map['theme_hero'].default_params
            )
        
        # 4b. Flexible Columns Block (Parent Container)
        if 'flex_columns' in definitions_map:
            flex_parent = BlockInstance.objects.create(
                definition=definitions_map['flex_columns'],
                page=example_page,
                parent=None,
                placement_key='main',
                sort_order=1,
                params={'col_widths': '50%, 50%'}
            )
            
            # 4c. Nested Markdown Block (Child 1 - Column 0)
            BlockInstance.objects.create(
                definition=definitions_map['markdown'],
                page=None,
                parent=flex_parent,
                placement_key='col_0',
                sort_order=0,
                params={'md': '## Imported Content\nThis is Column 1, generated during import.'}
            )

            # 4d. Nested Image Block (Child 2 - Column 1)
            BlockInstance.objects.create(
                definition=definitions_map['image'],
                page=None,
                parent=flex_parent,
                placement_key='col_1',
                sort_order=0,
                params={'src': 'https://placehold.co/400x200/475569/ffffff?text=Imported+Image', 'caption': 'In Column 2'}
            )


    return f"Successfully imported {len(inferred_definitions_data)} Block Definitions and one example Page for '{theme_name}'."