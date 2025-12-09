"""
Migration to consolidate all canonical block definitions.
This creates/updates the 19 core blocks that form the Hugo CMS vocabulary.
"""
from django.db import migrations


CANONICAL_BLOCKS = [
    # Content Blocks
    {
        'id': 'hero',
        'label': 'Hero Section',
        'icon': 'layout',
        'is_container': False,
        'default_params': {
            'title': 'Welcome',
            'subtitle': 'Your tagline here',
            'bgImage': '',
            'cta_text': '',
            'cta_url': ''
        },
        'schema': {
            'fields': [
                {'name': 'title', 'type': 'text', 'label': 'Title'},
                {'name': 'subtitle', 'type': 'text', 'label': 'Subtitle'},
                {'name': 'bgImage', 'type': 'image', 'label': 'Background Image'},
                {'name': 'cta_text', 'type': 'text', 'label': 'CTA Button Text'},
                {'name': 'cta_url', 'type': 'text', 'label': 'CTA Button URL'}
            ]
        }
    },
    {
        'id': 'text',
        'label': 'Text Block',
        'icon': 'type',
        'is_container': False,
        'default_params': {'content': '<p>Your content here...</p>'},
        'schema': {
            'fields': [
                {'name': 'content', 'type': 'richtext', 'label': 'Content'}
            ]
        }
    },
    {
        'id': 'markdown',
        'label': 'Markdown',
        'icon': 'file-text',
        'is_container': False,
        'default_params': {'md': '## Heading\n\nYour markdown content here.'},
        'schema': {
            'fields': [
                {'name': 'md', 'type': 'markdown', 'label': 'Markdown Content'}
            ]
        }
    },
    {
        'id': 'image',
        'label': 'Image',
        'icon': 'image',
        'is_container': False,
        'default_params': {'src': '', 'alt': '', 'caption': ''},
        'schema': {
            'fields': [
                {'name': 'src', 'type': 'image', 'label': 'Image'},
                {'name': 'alt', 'type': 'text', 'label': 'Alt Text'},
                {'name': 'caption', 'type': 'text', 'label': 'Caption'}
            ]
        }
    },
    {
        'id': 'button',
        'label': 'Button',
        'icon': 'mouse-pointer',
        'is_container': False,
        'default_params': {'text': 'Click Here', 'url': '#', 'style': 'primary'},
        'schema': {
            'fields': [
                {'name': 'text', 'type': 'text', 'label': 'Button Text'},
                {'name': 'url', 'type': 'url', 'label': 'URL'},
                {'name': 'style', 'type': 'select', 'label': 'Style', 'options': ['primary', 'secondary', 'outline']}
            ]
        }
    },
    {
        'id': 'quote',
        'label': 'Blockquote',
        'icon': 'quote',
        'is_container': False,
        'default_params': {'text': '', 'author': ''},
        'schema': {
            'fields': [
                {'name': 'text', 'type': 'textarea', 'label': 'Quote Text'},
                {'name': 'author', 'type': 'text', 'label': 'Author'}
            ]
        }
    },
    {
        'id': 'alert',
        'label': 'Alert Box',
        'icon': 'alert-triangle',
        'is_container': False,
        'default_params': {'type': 'info', 'message': 'Important message here.'},
        'schema': {
            'fields': [
                {'name': 'type', 'type': 'select', 'label': 'Type', 'options': ['info', 'warning', 'success', 'error']},
                {'name': 'message', 'type': 'textarea', 'label': 'Message'}
            ]
        }
    },
    {
        'id': 'youtube',
        'label': 'YouTube Embed',
        'icon': 'video',
        'is_container': False,
        'default_params': {'videoId': '', 'title': ''},
        'schema': {
            'fields': [
                {'name': 'videoId', 'type': 'text', 'label': 'Video ID'},
                {'name': 'title', 'type': 'text', 'label': 'Title'}
            ]
        }
    },
    {
        'id': 'html',
        'label': 'HTML Block',
        'icon': 'code',
        'is_container': False,
        'default_params': {'content': ''},
        'schema': {
            'fields': [
                {'name': 'content', 'type': 'code', 'label': 'HTML Content'}
            ]
        }
    },
    # Feature/Grid Blocks
    {
        'id': 'features_grid',
        'label': 'Features Grid',
        'icon': 'grid',
        'is_container': False,
        'default_params': {'items': [], 'columns': 3},
        'schema': {
            'fields': [
                {'name': 'items', 'type': 'array', 'label': 'Features', 'item_schema': {
                    'icon': 'text', 'title': 'text', 'description': 'textarea'
                }},
                {'name': 'columns', 'type': 'number', 'label': 'Columns'}
            ]
        }
    },
    {
        'id': 'accordion',
        'label': 'Accordion/FAQ',
        'icon': 'chevrons-down',
        'is_container': False,
        'default_params': {'items': [], 'allow_multiple': False},
        'schema': {
            'fields': [
                {'name': 'items', 'type': 'array', 'label': 'Items', 'item_schema': {
                    'title': 'text', 'content': 'richtext'
                }},
                {'name': 'allow_multiple', 'type': 'boolean', 'label': 'Allow Multiple Open'}
            ]
        }
    },
    {
        'id': 'flip_cards',
        'label': 'Flip Cards',
        'icon': 'rotate-3d',
        'is_container': False,
        'default_params': {'cards': [], 'columns': 3},
        'schema': {
            'fields': [
                {'name': 'cards', 'type': 'array', 'label': 'Cards', 'item_schema': {
                    'front_title': 'text', 'front_icon': 'text', 
                    'back_description': 'textarea', 'back_cta_text': 'text', 'back_cta_url': 'text'
                }},
                {'name': 'columns', 'type': 'number', 'label': 'Columns'}
            ]
        }
    },
    {
        'id': 'testimonial',
        'label': 'Testimonial',
        'icon': 'message-circle',
        'is_container': False,
        'default_params': {'quote': '', 'author': '', 'image': ''},
        'schema': {
            'fields': [
                {'name': 'quote', 'type': 'textarea', 'label': 'Quote'},
                {'name': 'author', 'type': 'text', 'label': 'Author'},
                {'name': 'image', 'type': 'image', 'label': 'Author Image'}
            ]
        }
    },
    # Navigation/Branding
    {
        'id': 'menu',
        'label': 'Navigation Menu',
        'icon': 'menu',
        'is_container': True,  # Supports nested blocks for slide-in sidebar
        'default_params': {'items': [], 'style': 'default', 'responsive': True, 'hamburgerDirection': 'dropdown'},
        'schema': {
            'fields': [
                {'name': 'items', 'type': 'array', 'label': 'Menu Items', 'item_schema': {
                    'label': 'text', 'url': 'text', 'type': 'select'
                }},
                {'name': 'style', 'type': 'select', 'label': 'Style', 'options': ['default', 'pills', 'underline']},
                {'name': 'responsive', 'type': 'boolean', 'label': 'Responsive'},
                {'name': 'hamburgerDirection', 'type': 'select', 'label': 'Mobile Menu Style', 'options': ['dropdown', 'slide-left', 'slide-right']}
            ]
        }
    },
    {
        'id': 'brand_logo',
        'label': 'Brand Logo',
        'icon': 'hexagon',
        'is_container': False,
        'default_params': {'brand_name': '', 'logo_image': '', 'tagline': '', 'link_url': '/'},
        'schema': {
            'fields': [
                {'name': 'brand_name', 'type': 'text', 'label': 'Brand Name'},
                {'name': 'logo_image', 'type': 'image', 'label': 'Logo Image'},
                {'name': 'tagline', 'type': 'text', 'label': 'Tagline'},
                {'name': 'link_url', 'type': 'url', 'label': 'Link URL'}
            ]
        }
    },
    # Social/Stats
    {
        'id': 'social_links',
        'label': 'Social Media Links',
        'icon': 'share',
        'is_container': False,
        'default_params': {'links': []},
        'schema': {
            'fields': [
                {'name': 'links', 'type': 'array', 'label': 'Social Links', 'item_schema': {
                    'platform': 'select', 'url': 'text'
                }}
            ]
        }
    },
    {
        'id': 'stats',
        'label': 'Stats Counter',
        'icon': 'bar-chart',
        'is_container': False,
        'default_params': {'items': [], 'animate': True},
        'schema': {
            'fields': [
                {'name': 'items', 'type': 'array', 'label': 'Stats', 'item_schema': {
                    'value': 'text', 'label': 'text', 'suffix': 'text'
                }},
                {'name': 'animate', 'type': 'boolean', 'label': 'Animate on Scroll'}
            ]
        }
    },
    {
        'id': 'process_steps',
        'label': 'Process Steps',
        'icon': 'list-ordered',
        'is_container': False,
        'default_params': {'steps': [], 'layout': 'vertical'},
        'schema': {
            'fields': [
                {'name': 'steps', 'type': 'array', 'label': 'Steps', 'item_schema': {
                    'title': 'text', 'description': 'textarea', 'icon': 'text'
                }},
                {'name': 'layout', 'type': 'select', 'label': 'Layout', 'options': ['vertical', 'horizontal']}
            ]
        }
    },
    # Container Blocks
    {
        'id': 'row',
        'label': 'Row (Flex)',
        'icon': 'layout-row',
        'is_container': True,
        'default_params': {'gap': '4', 'justify': 'start', 'align': 'stretch'},
        'schema': {
            'fields': [
                {'name': 'gap', 'type': 'select', 'label': 'Gap', 'options': ['0', '2', '4', '6', '8']},
                {'name': 'justify', 'type': 'select', 'label': 'Justify', 'options': ['start', 'center', 'end', 'between', 'around']},
                {'name': 'align', 'type': 'select', 'label': 'Align', 'options': ['start', 'center', 'end', 'stretch']}
            ]
        }
    },
    {
        'id': 'column',
        'label': 'Column',
        'icon': 'columns',
        'is_container': True,
        'default_params': {'width': 'auto'},
        'schema': {
            'fields': [
                {'name': 'width', 'type': 'text', 'label': 'Width (e.g. 50%, auto)'}
            ]
        }
    },
    {
        'id': 'carousel',
        'label': 'Carousel',
        'icon': 'layers',
        'is_container': True,
        'default_params': {'auto_advance': True, 'interval_seconds': 5, 'show_dots': True, 'show_arrows': True},
        'schema': {
            'fields': [
                {'name': 'auto_advance', 'type': 'boolean', 'label': 'Auto Advance'},
                {'name': 'interval_seconds', 'type': 'number', 'label': 'Interval (seconds)'},
                {'name': 'show_dots', 'type': 'boolean', 'label': 'Show Dots'},
                {'name': 'show_arrows', 'type': 'boolean', 'label': 'Show Arrows'}
            ]
        }
    },
    # Additional Blocks
    {
        'id': 'google_reviews',
        'label': 'Google Reviews',
        'icon': 'star',
        'is_container': False,
        'default_params': {'reviews': [], 'show_rating': True, 'columns': 3},
        'schema': {
            'fields': [
                {'name': 'reviews', 'type': 'array', 'label': 'Reviews', 'item_schema': {
                    'name': 'text', 'rating': 'number', 'text': 'textarea', 'date': 'text', 'image': 'image'
                }},
                {'name': 'show_rating', 'type': 'boolean', 'label': 'Show Rating'},
                {'name': 'columns', 'type': 'number', 'label': 'Columns'}
            ]
        }
    },
    {
        'id': 'flex_columns',
        'label': 'Flexible Columns',
        'icon': 'columns',
        'is_container': True,
        'default_params': {'col_widths': '50, 50'},
        'schema': {
            'fields': [
                {'name': 'col_widths', 'type': 'text', 'label': 'Column Widths (comma-separated percentages)'}
            ]
        }
    },
]


def create_canonical_blocks(apps, schema_editor):
    BlockDefinition = apps.get_model('hugo', 'BlockDefinition')
    
    for block in CANONICAL_BLOCKS:
        BlockDefinition.objects.update_or_create(
            id=block['id'],
            defaults={
                'label': block['label'],
                'icon': block['icon'],
                'is_container': block.get('is_container', False),
                'default_params': block['default_params'],
                'schema': block.get('schema', {}),
                'has_visual_preview': True
            }
        )


def reverse_canonical_blocks(apps, schema_editor):
    # Don't delete - just leave them in place
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('hugo', '0035_update_row_block'),
    ]

    operations = [
        migrations.RunPython(create_canonical_blocks, reverse_canonical_blocks),
    ]
