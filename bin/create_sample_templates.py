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
                'title': '',
                'layout': 'home',
                'blocks': [
                    {
                        'type': 'hero',
                        'placement_key': 'main',
                        'params': {
                            'title': '',
                            'subtitle': '',
                            'bgImage': '',
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
                                        'params': {'content': ''}
                                    },
                                    {
                                        'type': 'image',
                                        'params': {'src': '', 'alt': ''}
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
                                'params': {'content': '<h2></h2><p></p>'}
                            },
                            {
                                'type': 'features_grid',
                                'params': {
                                    'items': [],
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
                                'params': {'items': []}
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
                                'children': []
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
                                'params': {'content': '<h2>Ready to Begin?</h2><p></p>'}
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
                'title': '',
                'layout': 'home',
                'blocks': [
                    {
                        'type': 'hero',
                        'placement_key': 'main',
                        'params': {
                            'title': '',
                            'subtitle': '',
                            'bgImage': '',
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
                                'params': {'content': '<p class="text-center"></p>'}
                            },
                            {
                                'type': 'features_grid',
                                'params': {
                                    'items': [],
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
                                'params': {'content': '<h2></h2><p></p>'}
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
                                'params': {'steps': [], 'layout': 'vertical'}
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
                                'params': {'items': [], 'columns': 4}
                            }
                        ]
                    },
                    {
                        'type': 'stats',
                        'placement_key': 'main',
                        'params': {
                            'items': [],
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
                                'params': {'reviews': [], 'columns': 3}
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
                                'params': {'items': []}
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
                                'params': {'content': '<h2></h2><p></p>'}
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

# ============================================================================
# FOOD TRUCK V2 TEMPLATE (comprehensive best-practice food truck site)
# ============================================================================
foodtruckv2_template, created = SiteTemplate.objects.update_or_create(
    slug='food-truck-v2',
    defaults={
        'name': 'Food Trucks V2',
        'description': 'A comprehensive, conversion-optimized food truck template featuring header navigation, hero with CTA, value propositions, menu showcase, locations/schedule, catering services, brand story, social proof, and footer with social links.',
        'thumbnail_url': '',
        'base_css': '''
:root {
    --color-primary: #D84315;
    --color-secondary: #FF6F00;
    --color-accent: #FFC107;
    --color-bg-light: #FAFAFA;
    --color-bg-dark: #212121;
    --color-text: #212121;
    --color-text-light: #FFFFFF;
    --font-heading: "Montserrat", sans-serif;
    --font-body: "Roboto", sans-serif;
}
''',
        'pages_json': {
            'pages': [
                {
                    'slug': '/',
                    'title': 'Home',
                    'layout': 'home',
                    'blocks': [
                        # ===== MAIN ZONE =====
                        
                        # 1. Hero Section
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'welcome', 'id': 'hero'},
                            'children': [
                                {
                                    'type': 'hero',
                                    'params': {
                                        'title': '',
                                        'subtitle': '',
                                        'bgImage': '',
                                        'cta_text': 'View Menu',
                                        'cta_url': '/menu'
                                    }
                                }
                            ]
                        },
                        
                        # 2. Key Value Props / Highlights
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'default', 'id': 'highlights'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2 class="text-center"></h2><p class="text-center"></p>'}
                                },
                                {
                                    'type': 'features_grid',
                                    'params': {
                                        'items': [],
                                        'columns': 3
                                    }
                                }
                            ]
                        },
                        
                        # 3. Menu Overview
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'alt', 'id': 'menu'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2></h2>'}
                                },
                                {
                                    'type': 'markdown',
                                    'params': {'content': ''}
                                },
                                {
                                    'type': 'menu_grid',
                                    'params': {
                                        'items': [],
                                        'columns': 3,
                                        'show_images': True
                                    }
                                },
                                {
                                    'type': 'row',
                                    'params': {'justify': 'center', 'gap': '3'},
                                    'children': [
                                        {
                                            'type': 'button',
                                            'params': {
                                                'text': 'See Full Menu',
                                                'url': '/menu',
                                                'style': 'primary'
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        
                        # 4. Locations & Schedule
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'default', 'id': 'locations'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2></h2>'}
                                },
                                {
                                    'type': 'text',
                                    'params': {'content': ''}
                                },
                                {
                                    'type': 'process_steps',
                                    'params': {
                                        'steps': [],
                                        'layout': 'horizontal'
                                    }
                                },
                                {
                                    'type': 'embed',
                                    'params': {
                                        'embed_code': '',
                                        'height': '400px'
                                    }
                                }
                            ]
                        },
                        
                        # 5. Catering & Events
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'alt', 'id': 'catering'},
                            'children': [
                                {
                                    'type': 'flex_columns',
                                    'params': {'col_widths': '50, 50'},
                                    'children': [
                                        {
                                            'type': 'column',
                                            'children': [
                                                {
                                                    'type': 'text',
                                                    'params': {'content': '<h2></h2>'}
                                                },
                                                {
                                                    'type': 'markdown',
                                                    'params': {'content': ''}
                                                },
                                                {
                                                    'type': 'button',
                                                    'params': {
                                                        'text': 'Get Catering Info',
                                                        'url': '/catering',
                                                        'style': 'primary'
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'type': 'column',
                                            'children': [
                                                {
                                                    'type': 'accordion',
                                                    'params': {
                                                        'items': []
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        
                        # 6. About / Story Section
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'light', 'id': 'about'},
                            'children': [
                                {
                                    'type': 'flex_columns',
                                    'params': {'col_widths': '55, 45'},
                                    'children': [
                                        {
                                            'type': 'column',
                                            'children': [
                                                {
                                                    'type': 'text',
                                                    'params': {'content': '<h2></h2>'}
                                                },
                                                {
                                                    'type': 'markdown',
                                                    'params': {'content': ''}
                                                },
                                                {
                                                    'type': 'quote',
                                                    'params': {
                                                        'text': '',
                                                        'author': '',
                                                        'title': ''
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            'type': 'column',
                                            'children': [
                                                {
                                                    'type': 'image',
                                                    'params': {
                                                        'src': '',
                                                        'alt': ''
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        
                        # 7. Social Proof / Testimonials
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'alt', 'id': 'reviews'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2 class="text-center"></h2>'}
                                },
                                {
                                    'type': 'carousel',
                                    'params': {
                                        'auto_advance': True,
                                        'interval_seconds': 6
                                    },
                                    'children': []
                                },
                                {
                                    'type': 'google_reviews',
                                    'params': {
                                        'reviews': [],
                                        'columns': 3,
                                        'show_rating': True
                                    }
                                }
                            ]
                        },
                        
                        # 8. Stats Counter (optional - social proof with numbers)
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'cta'},
                            'children': [
                                {
                                    'type': 'stats_counter',
                                    'params': {
                                        'items': [],
                                        'animate': True
                                    }
                                }
                            ]
                        },
                        
                        # 9. Call-to-Action Band
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'cta', 'id': 'contact'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2 class="text-center"></h2><p class="text-center"></p>'}
                                },
                                {
                                    'type': 'row',
                                    'params': {'justify': 'center', 'gap': '4'},
                                    'children': [
                                        {
                                            'type': 'button',
                                            'params': {
                                                'text': 'Order Now',
                                                'url': '/menu',
                                                'style': 'primary'
                                            }
                                        },
                                        {
                                            'type': 'button',
                                            'params': {
                                                'text': 'Contact Us',
                                                'url': '/contact',
                                                'style': 'secondary'
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                
                # ===== ADDITIONAL PAGE: /menu/ =====
                {
                    'slug': '/menu',
                    'title': 'Menu',
                    'layout': 'single',
                    'blocks': [
                        {
                            'type': 'hero',
                            'placement_key': 'main',
                            'params': {
                                'title': '',
                                'subtitle': '',
                                'bgImage': '',
                                'cta_text': '',
                                'cta_url': ''
                            }
                        },
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'default'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2></h2>'}
                                },
                                {
                                    'type': 'menu_grid',
                                    'params': {
                                        'items': [],
                                        'columns': 3,
                                        'show_images': True
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
                                    'type': 'carousel',
                                    'params': {
                                        'auto_advance': True,
                                        'interval_seconds': 5
                                    },
                                    'children': []
                                }
                            ]
                        }
                    ]
                },
                
                # ===== ADDITIONAL PAGE: /catering/ =====
                {
                    'slug': '/catering',
                    'title': 'Catering',
                    'layout': 'contact',
                    'blocks': [
                        {
                            'type': 'hero',
                            'placement_key': 'main',
                            'params': {
                                'title': '',
                                'subtitle': '',
                                'bgImage': '',
                                'cta_text': '',
                                'cta_url': ''
                            }
                        },
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'default'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h2></h2>'}
                                },
                                {
                                    'type': 'markdown',
                                    'params': {'content': ''}
                                },
                                {
                                    'type': 'features_grid',
                                    'params': {
                                        'items': [],
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
                                    'params': {'content': '<h2></h2>'}
                                },
                                {
                                    'type': 'process_steps',
                                    'params': {
                                        'steps': [],
                                        'layout': 'vertical'
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
                                    'params': {'content': '<h2></h2>'}
                                },
                                {
                                    'type': 'accordion',
                                    'params': {
                                        'items': []
                                    }
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
                                    'params': {'content': '<h2></h2><p></p>'}
                                },
                                {
                                    'type': 'button',
                                    'params': {
                                        'text': 'Contact Us',
                                        'url': '/contact',
                                        'style': 'primary'
                                    }
                                }
                            ]
                        }
                    ]
                },
                
                # ===== ADDITIONAL PAGE: /contact/ =====
                {
                    'slug': '/contact',
                    'title': 'Contact',
                    'layout': 'contact',
                    'blocks': [
                        {
                            'type': 'section',
                            'placement_key': 'main',
                            'params': {'style': 'default'},
                            'children': [
                                {
                                    'type': 'text',
                                    'params': {'content': '<h1></h1>'}
                                },
                                {
                                    'type': 'text',
                                    'params': {'content': ''}
                                },
                                {
                                    'type': 'flex_columns',
                                    'params': {'col_widths': '60, 40'},
                                    'children': [
                                        {
                                            'type': 'column',
                                            'children': [
                                                {
                                                    'type': 'text',
                                                    'params': {'content': '<h3></h3>'}
                                                },
                                                {
                                                    'type': 'markdown',
                                                    'params': {'content': ''}
                                                }
                                            ]
                                        },
                                        {
                                            'type': 'column',
                                            'children': [
                                                {
                                                    'type': 'text',
                                                    'params': {'content': '<h3></h3>'}
                                                },
                                                {
                                                    'type': 'markdown',
                                                    'params': {'content': ''}
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            
            # ===== GLOBAL BLOCKS (Header & Footer) =====
            'global_blocks': [
                # Header
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
                                'logo_url': '',
                                'brand_name': '',
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
                                    {'label': 'Catering', 'url': '/catering', 'type': 'link'},
                                    {'label': 'Contact', 'url': '/contact', 'type': 'link'}
                                ],
                                'style': 'pills',
                                'responsive': True,
                                'hamburgerDirection': 'dropdown'
                            },
                            'children': []
                        }
                    ]
                },
                
                # Footer - Social Links
                {
                    'type': 'social_links',
                    'placement_key': 'footer',
                    'sort_order': 0,
                    'params': {
                        'links': []
                    },
                    'children': []
                },
                
                # Footer - Copyright
                {
                    'type': 'text',
                    'placement_key': 'footer',
                    'sort_order': 1,
                    'params': {
                        'content': '<p class="text-center"></p>'
                    },
                    'children': []
                },
                
                # Footer - Tagline
                {
                    'type': 'text',
                    'placement_key': 'footer',
                    'sort_order': 2,
                    'params': {
                        'content': '<p class="text-center"></p>'
                    },
                    'children': []
                }
            ]
        },
        'placeholder_schema': {
            # Business Identity
            'business_name': {'type': 'text', 'label': 'Business Name', 'required': True},
            'brand_logo_url': {'type': 'image', 'label': 'Brand Logo Image'},
            
            # Hero Section
            'hero_title': {'type': 'text', 'label': 'Hero Title', 'required': True},
            'hero_subtitle': {'type': 'text', 'label': 'Hero Subtitle'},
            'hero_bg_image': {'type': 'image', 'label': 'Hero Background Image'},
            'hero_cta_text': {'type': 'text', 'label': 'Hero CTA Button Text'},
            'hero_cta_url': {'type': 'text', 'label': 'Hero CTA Button URL'},
            
            # Value Propositions
            'value_props_title': {'type': 'text', 'label': 'Value Props Section Title'},
            'value_props_intro': {'type': 'textarea', 'label': 'Value Props Introduction'},
            'value_propositions': {'type': 'array', 'label': 'Value Propositions', 'item_schema': {'title': 'text', 'description': 'textarea', 'icon': 'text'}},
            
            # Menu Section
            'menu_section_title': {'type': 'text', 'label': 'Menu Section Title'},
            'menu_intro_text': {'type': 'textarea', 'label': 'Menu Introduction'},
            'menu_items': {'type': 'array', 'label': 'Menu Items', 'item_schema': {'name': 'text', 'description': 'textarea', 'price': 'text', 'image': 'image'}},
            'menu_cta_text': {'type': 'text', 'label': 'Menu CTA Button Text'},
            'menu_cta_url': {'type': 'text', 'label': 'Menu CTA Button URL'},
            
            # Locations & Schedule
            'locations_title': {'type': 'text', 'label': 'Locations Section Title'},
            'locations_description': {'type': 'richtext', 'label': 'Locations Description'},
            'find_us_steps': {'type': 'array', 'label': 'Find Us Steps', 'item_schema': {'title': 'text', 'description': 'textarea'}},
            'locations_embed_code': {'type': 'textarea', 'label': 'Map/Calendar Embed Code'},
            
            # Catering
            'catering_title': {'type': 'text', 'label': 'Catering Section Title'},
            'catering_description': {'type': 'richtext', 'label': 'Catering Description'},
            'catering_cta_text': {'type': 'text', 'label': 'Catering CTA Button Text'},
            'catering_cta_url': {'type': 'text', 'label': 'Catering CTA URL'},
            'catering_faqs': {'type': 'array', 'label': 'Catering FAQs', 'item_schema': {'title': 'text', 'content': 'richtext'}},
            
            # About/Story
            'about_title': {'type': 'text', 'label': 'About Section Title'},
            'about_story': {'type': 'richtext', 'label': 'About Story Text'},
            'about_image_url': {'type': 'image', 'label': 'About Section Image'},
            'about_image_alt': {'type': 'text', 'label': 'About Image Alt Text'},
            'founder_quote': {'type': 'textarea', 'label': 'Founder Quote'},
            'founder_name': {'type': 'text', 'label': 'Founder Name'},
            'founder_title': {'type': 'text', 'label': 'Founder Title'},
            
            # Testimonials & Reviews
            'testimonials_title': {'type': 'text', 'label': 'Testimonials Section Title'},
            'testimonial_slides': {'type': 'array', 'label': 'Testimonial Slides', 'item_schema': {'quote': 'textarea', 'author': 'text', 'title': 'text'}},
            'google_reviews': {'type': 'array', 'label': 'Google Reviews', 'item_schema': {'name': 'text', 'rating': 'number', 'text': 'textarea', 'date': 'text'}},
            
            # Stats
            'stats': {'type': 'array', 'label': 'Statistics', 'item_schema': {'value': 'text', 'label': 'text', 'suffix': 'text'}},
            
            # Final CTA
            'final_cta_title': {'type': 'text', 'label': 'Final CTA Title'},
            'final_cta_subtitle': {'type': 'textarea', 'label': 'Final CTA Subtitle'},
            'cta_primary_text': {'type': 'text', 'label': 'Primary CTA Button Text'},
            'cta_primary_url': {'type': 'text', 'label': 'Primary CTA Button URL'},
            'cta_secondary_text': {'type': 'text', 'label': 'Secondary CTA Button Text'},
            'cta_secondary_url': {'type': 'text', 'label': 'Secondary CTA Button URL'},
            
            # Footer
            'footer_copyright': {'type': 'text', 'label': 'Footer Copyright Text'},
            'footer_tagline': {'type': 'text', 'label': 'Footer Tagline'},
            'social_links': {'type': 'array', 'label': 'Social Media Links', 'item_schema': {'platform': 'text', 'url': 'text'}},
            
            # Menu Page
            'menu_page_title': {'type': 'text', 'label': 'Menu Page Title'},
            'menu_page_hero_title': {'type': 'text', 'label': 'Menu Page Hero Title'},
            'menu_page_hero_subtitle': {'type': 'text', 'label': 'Menu Page Hero Subtitle'},
            'menu_page_bg_image': {'type': 'image', 'label': 'Menu Page Background Image'},
            'menu_page_section_title': {'type': 'text', 'label': 'Menu Page Section Title'},
            'full_menu_items': {'type': 'array', 'label': 'Full Menu Items', 'item_schema': {'name': 'text', 'description': 'textarea', 'price': 'text', 'image': 'image'}},
            'menu_photos_slides': {'type': 'array', 'label': 'Menu Photo Slides', 'item_schema': {'image': 'image', 'caption': 'text'}},
            
            # Catering Page
            'catering_page_title': {'type': 'text', 'label': 'Catering Page Title'},
            'catering_page_hero_title': {'type': 'text', 'label': 'Catering Hero Title'},
            'catering_page_hero_subtitle': {'type': 'text', 'label': 'Catering Hero Subtitle'},
            'catering_page_bg_image': {'type': 'image', 'label': 'Catering Background Image'},
            'catering_page_intro_title': {'type': 'text', 'label': 'Catering Intro Title'},
            'catering_page_intro_text': {'type': 'richtext', 'label': 'Catering Intro Text'},
            'catering_event_types': {'type': 'array', 'label': 'Event Types', 'item_schema': {'title': 'text', 'description': 'textarea', 'icon': 'text'}},
            'catering_process_title': {'type': 'text', 'label': 'Catering Process Title'},
            'catering_process_steps': {'type': 'array', 'label': 'Catering Process Steps', 'item_schema': {'title': 'text', 'description': 'textarea'}},
            'catering_faq_title': {'type': 'text', 'label': 'Catering FAQ Title'},
            'catering_page_faqs': {'type': 'array', 'label': 'Catering FAQs', 'item_schema': {'title': 'text', 'content': 'richtext'}},
            'catering_contact_title': {'type': 'text', 'label': 'Catering Contact Title'},
            'catering_contact_text': {'type': 'textarea', 'label': 'Catering Contact Text'},
            'catering_contact_button': {'type': 'text', 'label': 'Contact Button Text'},
            
            # Contact Page
            'contact_page_title': {'type': 'text', 'label': 'Contact Page Title'},
            'contact_page_heading': {'type': 'text', 'label': 'Contact Page Heading'},
            'contact_page_instructions': {'type': 'richtext', 'label': 'Contact Instructions'},
            'contact_methods_title': {'type': 'text', 'label': 'Contact Methods Title'},
            'contact_methods_list': {'type': 'richtext', 'label': 'Contact Methods List'},
            'contact_hours_title': {'type': 'text', 'label': 'Contact Hours Title'},
            'contact_hours_info': {'type': 'richtext', 'label': 'Contact Hours Info'}
        },
        'is_featured': True,
        'is_public': True
    }
)
foodtruckv2_template.tags = ['food-truck', 'catering', 'restaurant', 'food', 'events', 'mobile-food', 'conversion-optimized']
foodtruckv2_template.save()
print(f"{'Created' if created else 'Updated'} food-truck-v2 template")

print("\nDone! Created 3 templates.")
