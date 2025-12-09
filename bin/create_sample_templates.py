#!/usr/bin/env python
"""
Script to create sample SiteTemplates based on cairnscounselingcenter.com and mambotruck.com.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import SiteTemplate

# ============================================================================
# THERAPIST TEMPLATE (based on cairnscounselingcenter.com)
# ============================================================================
therapist_template, created = SiteTemplate.objects.update_or_create(
    slug='therapist-professional',
    defaults={
        'name': 'Professional Therapist',
        'description': 'A warm, professional template for therapists and counselors. Features hero section, about content, services accordion, testimonials carousel, and contact CTA.',
        'thumbnail_url': '',
        'base_css': '''
:root {
    --color-primary: #4A7C6F;
    --color-secondary: #2D4A3E;
    --color-accent: #8FB3A5;
    --color-bg-light: #F9FAFB;
    --color-text: #1F2937;
    --font-heading: "Playfair Display", serif;
    --font-body: "Open Sans", sans-serif;
}
''',
        'pages_json': [
            {
                'slug': '/',
                'title': '{{business_name}}',
                'layout': 'home',
                'blocks': [
                    {
                        'type': 'hero',
                        'placement_key': 'main',
                        'params': {
                            'title': '{{business_name}}',
                            'subtitle': '{{tagline}}',
                            'bgImage': '{{hero_image}}',
                            'cta_text': 'Book a Session',
                            'cta_url': '/contact'
                        }
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'welcome'},
                        'children': [
                            {
                                'type': 'flex_columns',
                                'params': {'col_widths': '60, 40'},
                                'children': [
                                    {
                                        'type': 'text',
                                        'params': {'content': '{{about_intro}}'}
                                    },
                                    {
                                        'type': 'image',
                                        'params': {'src': '{{about_image}}', 'alt': '{{business_name}}'}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'alt'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>{{approach_title}}</h2><p>{{approach_description}}</p>'}
                            },
                            {
                                'type': 'features_grid',
                                'params': {
                                    'items': '{{approach_features}}',
                                    'columns': 3
                                }
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'default'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>Services</h2>'}
                            },
                            {
                                'type': 'accordion',
                                'params': {'items': '{{services_faq}}'}
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'alt'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>What Clients Say</h2>'}
                            },
                            {
                                'type': 'carousel',
                                'params': {'auto_advance': True, 'interval_seconds': 8},
                                'children': '{{testimonials}}'
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'cta'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>Ready to Begin?</h2><p>{{cta_description}}</p>'}
                            },
                            {
                                'type': 'row',
                                'params': {'justify': 'center', 'gap': '4'},
                                'children': [
                                    {
                                        'type': 'button',
                                        'params': {'text': 'View Services', 'url': '/services', 'style': 'primary'}
                                    },
                                    {
                                        'type': 'button',
                                        'params': {'text': 'Free Consultation', 'url': '/contact', 'style': 'secondary'}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        'placeholder_schema': {
            'business_name': {'type': 'text', 'label': 'Business Name', 'required': True},
            'tagline': {'type': 'text', 'label': 'Tagline/Subtitle', 'required': True},
            'hero_image': {'type': 'image', 'label': 'Hero Background Image'},
            'about_intro': {'type': 'richtext', 'label': 'About Introduction'},
            'about_image': {'type': 'image', 'label': 'About Section Image'},
            'approach_title': {'type': 'text', 'label': 'Approach Section Title'},
            'approach_description': {'type': 'textarea', 'label': 'Approach Description'},
            'approach_features': {'type': 'array', 'label': 'Approach Features', 'item_schema': {'title': 'text', 'description': 'textarea', 'icon': 'text'}},
            'services_faq': {'type': 'array', 'label': 'Services (FAQ format)', 'item_schema': {'title': 'text', 'content': 'richtext'}},
            'testimonials': {'type': 'array', 'label': 'Client Testimonials', 'item_schema': {'quote': 'textarea', 'author': 'text'}},
            'cta_description': {'type': 'textarea', 'label': 'CTA Section Description'}
        },
        'is_featured': True,
        'is_public': True
    }
)
therapist_template.tags = ['therapy', 'counseling', 'healthcare', 'mental-health', 'professional', 'services']
therapist_template.save()
print(f"{'Created' if created else 'Updated'} therapist-professional template")

# ============================================================================
# FOOD TRUCK TEMPLATE (based on mambotruck.com)
# ============================================================================
foodtruck_template, created = SiteTemplate.objects.update_or_create(
    slug='food-truck-catering',
    defaults={
        'name': 'Food Truck & Catering',
        'description': 'A vibrant, engaging template for food trucks and catering businesses. Features hero with CTA, features grid, process steps, menu highlights, stats counter, testimonials, and FAQ.',
        'thumbnail_url': '',
        'base_css': '''
:root {
    --color-primary: #E85D04;
    --color-secondary: #F48C06;
    --color-accent: #FAA307;
    --color-bg-dark: #1A1A2E;
    --color-text: #16213E;
    --font-heading: "Poppins", sans-serif;
    --font-body: "Inter", sans-serif;
}
''',
        'pages_json': [
            {
                'slug': '/',
                'title': '{{business_name}}',
                'layout': 'home',
                'blocks': [
                    {
                        'type': 'hero',
                        'placement_key': 'main',
                        'params': {
                            'title': '{{headline}}',
                            'subtitle': '{{tagline}}',
                            'bgImage': '{{hero_image}}',
                            'cta_text': 'Book the Truck',
                            'cta_url': '/packages'
                        }
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'default'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<p class="text-center">{{intro_text}}</p>'}
                            },
                            {
                                'type': 'features_grid',
                                'params': {
                                    'items': '{{key_features}}',
                                    'columns': 3
                                }
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'alt'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>{{problem_headline}}</h2><p>{{problem_description}}</p>'}
                            },
                            {
                                'type': 'button',
                                'params': {'text': 'Book the Truck', 'url': '/packages', 'style': 'primary'}
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'default'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': "<h2>Here's How It Works</h2>"}
                            },
                            {
                                'type': 'process_steps',
                                'params': {'steps': '{{process_steps}}', 'layout': 'vertical'}
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'alt'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>Our Menu Favorites</h2>'}
                            },
                            {
                                'type': 'features_grid',
                                'params': {'items': '{{menu_items}}', 'columns': 4}
                            }
                        ]
                    },
                    {
                        'type': 'stats',
                        'placement_key': 'main',
                        'params': {
                            'items': '{{stats}}',
                            'animate': True
                        }
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'default'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>What Customers Say</h2>'}
                            },
                            {
                                'type': 'google_reviews',
                                'params': {'reviews': '{{reviews}}', 'columns': 3}
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'alt'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>Frequently Asked Questions</h2>'}
                            },
                            {
                                'type': 'accordion',
                                'params': {'items': '{{faq_items}}'}
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'placement_key': 'main',
                        'params': {'style': 'cta'},
                        'children': [
                            {
                                'type': 'text',
                                'params': {'content': '<h2>{{cta_headline}}</h2><p>{{cta_description}}</p>'}
                            },
                            {
                                'type': 'button',
                                'params': {'text': 'Book the Truck', 'url': '/packages', 'style': 'primary'}
                            }
                        ]
                    }
                ]
            }
        ],
        'placeholder_schema': {
            'business_name': {'type': 'text', 'label': 'Business Name', 'required': True},
            'headline': {'type': 'text', 'label': 'Hero Headline', 'required': True},
            'tagline': {'type': 'text', 'label': 'Tagline'},
            'hero_image': {'type': 'image', 'label': 'Hero Background Image'},
            'intro_text': {'type': 'textarea', 'label': 'Introduction Text'},
            'key_features': {'type': 'array', 'label': 'Key Features', 'item_schema': {'title': 'text', 'description': 'textarea', 'icon': 'text'}},
            'problem_headline': {'type': 'text', 'label': 'Problem Section Headline'},
            'problem_description': {'type': 'textarea', 'label': 'Problem Description'},
            'process_steps': {'type': 'array', 'label': 'Process Steps', 'item_schema': {'title': 'text', 'description': 'textarea'}},
            'menu_items': {'type': 'array', 'label': 'Menu Items', 'item_schema': {'title': 'text', 'description': 'text', 'image': 'image'}},
            'stats': {'type': 'array', 'label': 'Stats', 'item_schema': {'value': 'text', 'label': 'text', 'suffix': 'text'}},
            'reviews': {'type': 'array', 'label': 'Customer Reviews', 'item_schema': {'name': 'text', 'rating': 'number', 'text': 'textarea'}},
            'faq_items': {'type': 'array', 'label': 'FAQ Items', 'item_schema': {'title': 'text', 'content': 'richtext'}},
            'cta_headline': {'type': 'text', 'label': 'CTA Headline'},
            'cta_description': {'type': 'textarea', 'label': 'CTA Description'}
        },
        'is_featured': True,
        'is_public': True
    }
)
foodtruck_template.tags = ['food-truck', 'catering', 'restaurant', 'food', 'events', 'mobile-food']
foodtruck_template.save()
print(f"{'Created' if created else 'Updated'} food-truck-catering template")

print("\nDone! Created 2 templates.")
