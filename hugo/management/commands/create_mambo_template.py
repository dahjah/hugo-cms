"""
Create the Mambo Truck site template directly in the database.

This creates a food truck/catering template based on mambotruck.com.

Usage:
    python manage.py create_mambo_template
    python manage.py create_mambo_template --use-dembrandt  # Extract from live site
"""
from django.core.management.base import BaseCommand
from hugo.models import SiteTemplate
from hugo.utils.extract_design_tokens import run_dembrandt, tokens_to_base_css, extract_logo_url


# Fallback CSS if dembrandt fails
MAMBO_CSS_FALLBACK = """
:root {
  /* Color Palette - Bold and vibrant */
  --color-primary: #E63946;      /* Vibrant red */
  --color-primary-dark: #C5303C;
  --color-secondary: #1D3557;    /* Deep navy */
  --color-accent: #F4A261;       /* Warm orange */
  --color-background: #FFFFFF;
  --color-surface: #F8F9FA;
  --color-text: #1D3557;
  --color-text-muted: #6C757D;
  
  /* Typography */
  --font-heading: 'Poppins', sans-serif;
  --font-body: 'Open Sans', sans-serif;
  
  /* Spacing */
  --section-padding: 5rem 2rem;
  --container-max-width: 1200px;
}

body {
  font-family: var(--font-body);
  color: var(--color-text);
  background-color: var(--color-background);
  line-height: 1.6;
}

h1, h2, h3, h4 {
  font-family: var(--font-heading);
  font-weight: 700;
}

.hero-section {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  text-align: center;
  padding: 6rem 2rem;
}

.hero-section h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.section {
  padding: var(--section-padding);
  max-width: var(--container-max-width);
  margin: 0 auto;
}

.section-alt {
  background-color: var(--color-surface);
}

.cta-button {
  display: inline-block;
  background-color: var(--color-accent);
  color: var(--color-text);
  padding: 1rem 2.5rem;
  border-radius: 50px;
  text-decoration: none;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all 0.3s ease;
}

.cta-button:hover {
  background-color: var(--color-primary);
  color: white;
  transform: translateY(-2px);
}

.stats-grid {
  display: flex;
  justify-content: center;
  gap: 4rem;
  text-align: center;
}

.stat-item .value {
  font-size: 3rem;
  font-weight: 700;
  color: var(--color-primary);
}

.stat-item .label {
  color: var(--color-text-muted);
}
"""


def get_mambo_css():
    """Extract CSS from live site using dembrandt, with fallback."""
    try:
        tokens = run_dembrandt("https://mambotruck.com")
        if tokens:
            return tokens_to_base_css(tokens)
    except Exception as e:
        print(f"Dembrandt extraction failed: {e}")
    return MAMBO_CSS_FALLBACK


def get_mambo_logo():
    """Extract logo URL from live site using dembrandt."""
    try:
        tokens = run_dembrandt("https://mambotruck.com")
        if tokens:
            return extract_logo_url(tokens)
    except Exception:
        pass
    return None


# Serialized pages with blocks structure
MAMBO_PAGES_JSON = {
    'pages': [
        {
            'slug': '/',
            'title': 'Home',
            'layout': 'single',
            'description': 'Food truck catering for events everyone will remember',
            'blocks': [
                {
                    'type': 'hero',
                    'placement_key': 'main',
                    'sort_order': 0,
                    'params': {
                        'title': "{{ headline }}",
                        'subtitle': "{{ subheadline }}",
                        'bgImage': '',
                        'cta_text': 'Book the Truck',
                        'cta_url': '/packages'
                    },
                    'children': []
                },
                {
                    'type': 'features_grid',
                    'placement_key': 'main',
                    'sort_order': 1,
                    'params': {
                        'columns': 3,
                        'items': [
                            {'icon': 'clock', 'title': 'Reliable Service', 'description': 'Dependable scheduling and clear communication ensure your catering is one less thing to worry about.'},
                            {'icon': 'truck', 'title': 'Interactive Experience', 'description': 'The food truck itself is a fun, engaging centerpiece for your event, adding personality and flair.'},
                            {'icon': 'dollar-sign', 'title': 'Transparent Pricing', 'description': 'Clear, upfront pricing eliminates unexpected costs and ensures you can plan confidently within your budget.'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 2,
                    'params': {
                        'content': '<h2>{{ pain_point_headline }}</h2><p>{{ pain_point_description }}</p>'
                    },
                    'children': []
                },
                {
                    'type': 'process_steps',
                    'placement_key': 'main',
                    'sort_order': 3,
                    'params': {
                        'layout': 'horizontal',
                        'steps': [
                            {'title': '1. Book Your Experience', 'description': 'Pick your ideal package or request a custom option, confirm your date, and provide us with the event details.', 'icon': 'calendar'},
                            {'title': '2. Stay Connected', 'description': 'Our team keeps you updated with seamless communication as your event day gets closer.', 'icon': 'message-circle'},
                            {'title': '3. Savor the Celebration', 'description': 'When the day arrives, our truck rolls in to serve your guests with vibrant cuisine.', 'icon': 'party-popper'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'stats',
                    'placement_key': 'main',
                    'sort_order': 4,
                    'params': {
                        'animate': True,
                        'items': [
                            {'value': '{{ stat_1_value }}', 'label': '{{ stat_1_label }}', 'suffix': '+'},
                            {'value': '{{ stat_2_value }}', 'label': '{{ stat_2_label }}', 'suffix': '+'},
                            {'value': '{{ stat_3_value }}', 'label': '{{ stat_3_label }}', 'suffix': '+'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 5,
                    'params': {
                        'content': '<h2>What Customers Are Saying</h2>'
                    },
                    'children': []
                },
                {
                    'type': 'carousel',
                    'placement_key': 'main',
                    'sort_order': 6,
                    'params': {
                        'auto_advance': True,
                        'interval_seconds': 6,
                        'show_dots': True,
                        'show_arrows': True,
                        'slides': [
                            {
                                'id': 'slide_1',
                                'children': [
                                    {
                                        'id': 'testimonial_1',
                                        'type': 'testimonial',
                                        'params': {
                                            'quote': '{{ testimonial_1_quote }}',
                                            'author': '{{ testimonial_1_author }}',
                                            'image': ''
                                        },
                                        'children': None,
                                        'placement_key': 'slide',
                                        'sort_order': 0
                                    }
                                ]
                            },
                            {
                                'id': 'slide_2',
                                'children': [
                                    {
                                        'id': 'testimonial_2',
                                        'type': 'testimonial',
                                        'params': {
                                            'quote': '{{ testimonial_2_quote }}',
                                            'author': '{{ testimonial_2_author }}',
                                            'image': ''
                                        },
                                        'children': None,
                                        'placement_key': 'slide',
                                        'sort_order': 0
                                    }
                                ]
                            }
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'accordion',
                    'placement_key': 'main',
                    'sort_order': 7,
                    'params': {
                        'allow_multiple': False,
                        'items': [
                            {'title': 'Will the food be good enough for my guests?', 'content': 'Absolutely! Our menu is crafted with bold, fresh flavors designed to impress even the pickiest eaters.'},
                            {'title': 'Will the food truck arrive on time?', 'content': 'Yes! Punctuality is our priority. We coordinate logistics well in advance and stay in communication with you.'},
                            {'title': 'What if the catering costs exceed my budget?', 'content': 'We offer customizable packages to fit a variety of budgets without compromising on quality.'},
                            {'title': 'Can you accommodate dietary restrictions?', 'content': 'Yes! We offer vegetarian, vegan, and gluten-free options to ensure all your guests can enjoy our food.'},
                            {'title': 'Is a food truck appropriate for formal events?', 'content': 'Definitely! Our vibrant food truck adds a unique and memorable touch to any event, formal or casual.'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 8,
                    'params': {
                        'content': '<h2>Not Quite Ready?</h2><p>Contact us to explore your options or ask questions.</p>'
                    },
                    'children': []
                },
                {
                    'type': 'button',
                    'placement_key': 'main',
                    'sort_order': 9,
                    'params': {
                        'text': 'Book the Truck',
                        'url': '/packages',
                        'style': 'primary'
                    },
                    'children': []
                }
            ]
        },
        {
            'slug': '/menu',
            'title': 'Our Menu',
            'layout': 'single',
            'description': 'Explore our delicious menu offerings',
            'blocks': [
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 0,
                    'params': {
                        'content': '<h1>Our Menu</h1><p>{{ menu_intro }}</p>'
                    },
                    'children': []
                },
                {
                    'type': 'menu_grid',
                    'placement_key': 'main',
                    'sort_order': 1,
                    'params': {
                        'title': 'Menu Favorites',
                        'items': [
                            {'name': '{{ menu_item_1_name }}', 'image': '{{ menu_item_1_image }}', 'description': '{{ menu_item_1_desc }}'},
                            {'name': '{{ menu_item_2_name }}', 'image': '{{ menu_item_2_image }}', 'description': '{{ menu_item_2_desc }}'},
                            {'name': '{{ menu_item_3_name }}', 'image': '{{ menu_item_3_image }}', 'description': '{{ menu_item_3_desc }}'},
                            {'name': '{{ menu_item_4_name }}', 'image': '{{ menu_item_4_image }}', 'description': '{{ menu_item_4_desc }}'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 2,
                    'params': {
                        'content': '<h2>Ready to Book?</h2><p>Check out our catering packages for your next event.</p>'
                    },
                    'children': []
                },
                {
                    'type': 'row',
                    'placement_key': 'main',
                    'sort_order': 3,
                    'params': {
                        'gap': '4',
                        'justify': 'center',
                        'align': 'center'
                    },
                    'children': [
                        {
                            'type': 'button',
                            'placement_key': 'column',
                            'sort_order': 0,
                            'params': {'text': 'View Packages', 'url': '/packages', 'style': 'primary'},
                            'children': []
                        },
                        {
                            'type': 'button',
                            'placement_key': 'column',
                            'sort_order': 1,
                            'params': {'text': 'Contact Us', 'url': '#contact', 'style': 'secondary'},
                            'children': []
                        }
                    ]
                }
            ]
        }
    ],
    'global_blocks': [
        {
            'type': 'row',
            'placement_key': 'header',
            'sort_order': 0,
            'params': {
                'gap': '4',
                'justify': 'space-between',
                'align': 'center'
            },
            'children': [
                {
                    'type': 'brand_logo',
                    'placement_key': 'column',
                    'sort_order': 0,
                    'params': {
                        'brand_name': '{{ business_name }}',
                        'logo_image': '',
                        'tagline': '',
                        'link_url': '/'
                    },
                    'children': []
                },
                {
                    'type': 'menu',
                    'placement_key': 'column',
                    'sort_order': 1,
                    'params': {
                        'items': [
                            {'label': 'Home', 'url': '/', 'type': 'link'},
                            {'label': 'Menu', 'url': '/menu', 'type': 'link'},
                            {'label': 'Packages', 'url': '/packages', 'type': 'link'},
                            {'label': 'About', 'url': '/about', 'type': 'link'},
                            {'label': 'Contact', 'url': '#contact', 'type': 'link'}
                        ],
                        'style': 'pills',
                        'responsive': True,
                        'hamburgerDirection': 'dropdown'
                    },
                    'children': []
                }
            ]
        },
        {
            'type': 'text',
            'placement_key': 'footer',
            'sort_order': 0,
            'params': {
                'content': '<p>{{ address }}</p><p>{{ phone }}</p>'
            },
            'children': []
        },
        {
            'type': 'social_links',
            'placement_key': 'footer',
            'sort_order': 1,
            'params': {
                'links': [
                    {'platform': 'facebook', 'url': '{{ facebook_url }}'},
                    {'platform': 'instagram', 'url': '{{ instagram_url }}'}
                ]
            },
            'children': []
        },
        {
            'type': 'text',
            'placement_key': 'footer',
            'sort_order': 2,
            'params': {
                'content': '<p>© 2025 {{ business_name }}. All Rights Reserved.</p>'
            },
            'children': []
        }
    ]
}

# Placeholder schema for LLM content filling
MAMBO_PLACEHOLDER_SCHEMA = {
    'business_name': {'type': 'text', 'description': 'Name of the food truck / catering business'},
    'headline': {'type': 'text', 'description': 'Main hero headline (e.g., "Food Truck Catering for Events Everyone Will Remember")'},
    'subheadline': {'type': 'text', 'description': 'Supporting subtitle under the headline'},
    'pain_point_headline': {'type': 'text', 'description': 'Headline addressing customer pain points'},
    'pain_point_description': {'type': 'richtext', 'description': 'Description of the problem you solve'},
    'stat_1_value': {'type': 'text', 'description': 'First stat number (e.g., "35k")'},
    'stat_1_label': {'type': 'text', 'description': 'First stat label (e.g., "Meals Served")'},
    'stat_2_value': {'type': 'text', 'description': 'Second stat number (e.g., "2k")'},
    'stat_2_label': {'type': 'text', 'description': 'Second stat label (e.g., "Happy Clients")'},
    'stat_3_value': {'type': 'text', 'description': 'Third stat number (e.g., "5")'},
    'stat_3_label': {'type': 'text', 'description': 'Third stat label (e.g., "Years of Experience")'},
    'testimonial_1_quote': {'type': 'text', 'description': 'First testimonial quote'},
    'testimonial_1_author': {'type': 'text', 'description': 'First testimonial author'},
    'testimonial_2_quote': {'type': 'text', 'description': 'Second testimonial quote'},
    'testimonial_2_author': {'type': 'text', 'description': 'Second testimonial author'},
    'menu_intro': {'type': 'text', 'description': 'Introduction text for the Menu page'},
    'menu_item_1_name': {'type': 'text', 'description': 'First menu item name'},
    'menu_item_1_image': {'type': 'url', 'description': 'First menu item image URL'},
    'menu_item_1_desc': {'type': 'text', 'description': 'First menu item description'},
    'menu_item_2_name': {'type': 'text', 'description': 'Second menu item name'},
    'menu_item_2_image': {'type': 'url', 'description': 'Second menu item image URL'},
    'menu_item_2_desc': {'type': 'text', 'description': 'Second menu item description'},
    'menu_item_3_name': {'type': 'text', 'description': 'Third menu item name'},
    'menu_item_3_image': {'type': 'url', 'description': 'Third menu item image URL'},
    'menu_item_3_desc': {'type': 'text', 'description': 'Third menu item description'},
    'menu_item_4_name': {'type': 'text', 'description': 'Fourth menu item name'},
    'menu_item_4_image': {'type': 'url', 'description': 'Fourth menu item image URL'},
    'menu_item_4_desc': {'type': 'text', 'description': 'Fourth menu item description'},
    'address': {'type': 'text', 'description': 'Business address'},
    'phone': {'type': 'text', 'description': 'Contact phone number'},
    'facebook_url': {'type': 'url', 'description': 'Facebook page URL'},
    'instagram_url': {'type': 'url', 'description': 'Instagram profile URL'}
}


class Command(BaseCommand):
    help = 'Create the Mambo Truck site template in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-dembrandt',
            action='store_true',
            help='Extract CSS from live site using dembrandt (slower but more accurate)'
        )

    def handle(self, *args, **options):
        # Get CSS - use dembrandt if requested, otherwise use fallback
        if options.get('use_dembrandt'):
            self.stdout.write('Extracting design tokens from live site...')
            base_css = get_mambo_css()
            logo_url = get_mambo_logo()
            self.stdout.write(self.style.SUCCESS(f'Extracted CSS and logo: {logo_url}'))
        else:
            base_css = MAMBO_CSS_FALLBACK
            logo_url = None
        
        template, created = SiteTemplate.objects.update_or_create(
            slug='mambo-food-truck',
            defaults={
                'name': "Food Truck / Catering",
                'description': 'A bold, vibrant template for food trucks, catering businesses, and mobile food vendors. Features hero with CTA, features grid, process steps, stats counter, testimonials carousel, and FAQ accordion.',
                'tags': ['food-truck', 'catering', 'restaurant', 'events', 'food-service'],
                'base_css': base_css,
                'pages_json': MAMBO_PAGES_JSON,
                'placeholder_schema': MAMBO_PLACEHOLDER_SCHEMA,
                'is_featured': True,
                'is_public': True,
                'created_by': 'system'
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{action} template: {template.name} (slug: {template.slug})\n'
            f'  Tags: {template.tags}\n'
            f'  Pages: {len(template.pages_json.get("pages", []))}\n'
            f'  Global blocks: {len(template.pages_json.get("global_blocks", []))}\n'
            f'  Placeholders: {len(template.placeholder_schema)}'
        ))
