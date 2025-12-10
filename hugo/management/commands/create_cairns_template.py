"""
Create the Cairn's Counseling site template directly in the database.

This creates a therapist/healthcare template based on cairnscounselingcenter.com.

Usage:
    python manage.py create_cairns_template
"""
from django.core.management.base import BaseCommand
from hugo.models import SiteTemplate
from hugo.utils.extract_design_tokens import run_dembrandt, tokens_to_base_css, extract_logo_url


# Fallback CSS if dembrandt fails
CAIRNS_CSS_FALLBACK = """
:root {
  /* Color Palette - Calming earth tones */
  --color-primary: #5B7B6F;      /* Sage green */
  --color-primary-dark: #4A6A5E;
  --color-secondary: #8B7355;    /* Warm brown */
  --color-accent: #C4A77D;       /* Soft gold */
  --color-background: #FAF9F6;   /* Off-white */
  --color-surface: #FFFFFF;
  --color-text: #2C3E36;
  --color-text-muted: #6B7B73;
  
  /* Typography */
  --font-heading: 'Cormorant Garamond', serif;
  --font-body: 'Open Sans', sans-serif;
  
  /* Spacing */
  --section-padding: 5rem 2rem;
  --container-max-width: 1200px;
}

body {
  font-family: var(--font-body);
  color: var(--color-text);
  background-color: var(--color-background);
  line-height: 1.7;
}

h1, h2, h3, h4 {
  font-family: var(--font-heading);
  font-weight: 500;
}

.hero-section {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  text-align: center;
  padding: 6rem 2rem;
}

.hero-section h1 {
  font-size: 3.5rem;
  margin-bottom: 1rem;
}

.hero-section .subtitle {
  font-size: 1.5rem;
  opacity: 0.9;
}

.section {
  padding: var(--section-padding);
  max-width: var(--container-max-width);
  margin: 0 auto;
}

.cta-button {
  display: inline-block;
  background-color: var(--color-accent);
  color: var(--color-text);
  padding: 1rem 2rem;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 600;
  transition: background-color 0.3s ease;
}

.cta-button:hover {
  background-color: var(--color-secondary);
  color: white;
}
"""


def get_cairns_css():
    """Extract CSS from live site using dembrandt, with fallback."""
    try:
        tokens = run_dembrandt("https://cairnscounselingcenter.com")
        if tokens:
            return tokens_to_base_css(tokens)
    except Exception as e:
        print(f"Dembrandt extraction failed: {e}")
    return CAIRNS_CSS_FALLBACK


def get_cairns_logo():
    """Extract logo URL from live site using dembrandt."""
    try:
        tokens = run_dembrandt("https://cairnscounselingcenter.com")
        if tokens:
            return extract_logo_url(tokens)
    except Exception:
        pass
    return None

# Serialized pages with blocks structure
CAIRNS_PAGES_JSON = {
    'pages': [
        {
            'slug': '/',
            'title': 'Home',
            'layout': 'single',
            'description': 'A safe space to find healing, transformation, and growth',
            'blocks': [
                {
                    'type': 'hero',
                    'placement_key': 'main',
                    'sort_order': 0,
                    'params': {
                        'title': "{{ business_name }}",
                        'subtitle': "{{ tagline }}",
                        'bgImage': '',
                        'cta_text': 'Schedule a Consultation',
                        'cta_url': '#contact'
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 1,
                    'params': {
                        'content': '<h2>My Approach to Healing</h2><p>{{ about_approach }}</p>'
                    },
                    'children': []
                },
                {
                    'type': 'features_grid',
                    'placement_key': 'main',
                    'sort_order': 2,
                    'params': {
                        'columns': 2,
                        'items': [
                            {'icon': 'heart', 'title': 'Safe Space', 'description': 'A nurturing environment where you can process your most difficult struggles'},
                            {'icon': 'users', 'title': 'Collaborative Partnership', 'description': 'Work together to discover your strengths and goals'},
                            {'icon': 'target', 'title': 'Root Cause Healing', 'description': 'Go beyond symptom management to lasting transformation'},
                            {'icon': 'compass', 'title': 'Inner Wisdom', 'description': 'Guiding you to your own insights for lasting change'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 3,
                    'params': {
                        'content': '<h2>My Treatment Philosophy</h2><p>{{ treatment_philosophy }}</p>'
                    },
                    'children': []
                },
                {
                    'type': 'row',
                    'placement_key': 'main',
                    'sort_order': 4,
                    'params': {
                        'gap': '6',
                        'justify': 'center',
                        'align': 'stretch'
                    },
                    'children': [
                        {
                            'type': 'column',
                            'placement_key': 'column',
                            'sort_order': 0,
                            'params': {'width': '33%'},
                            'children': [
                                {
                                    'type': 'text',
                                    'placement_key': 'blocks',
                                    'sort_order': 0,
                                    'params': {'content': '<h3>Healing</h3><p>Creating a safe space to process trauma, grief, and difficult emotions</p>'},
                                    'children': []
                                }
                            ]
                        },
                        {
                            'type': 'column',
                            'placement_key': 'column',
                            'sort_order': 1,
                            'params': {'width': '33%'},
                            'children': [
                                {
                                    'type': 'text',
                                    'placement_key': 'blocks',
                                    'sort_order': 0,
                                    'params': {'content': '<h3>Transformation</h3><p>Discovering your inner wisdom and resolving root causes</p>'},
                                    'children': []
                                }
                            ]
                        },
                        {
                            'type': 'column',
                            'placement_key': 'column',
                            'sort_order': 2,
                            'params': {'width': '33%'},
                            'children': [
                                {
                                    'type': 'text',
                                    'placement_key': 'blocks',
                                    'sort_order': 0,
                                    'params': {'content': '<h3>Growth</h3><p>Building new skills and confidence for lasting change</p>'},
                                    'children': []
                                }
                            ]
                        }
                    ]
                },
                {
                    'type': 'carousel',
                    'placement_key': 'main',
                    'sort_order': 5,
                    'params': {
                        'auto_advance': True,
                        'interval_seconds': 8,
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
                            },
                            {
                                'id': 'slide_3',
                                'children': [
                                    {
                                        'id': 'testimonial_3',
                                        'type': 'testimonial',
                                        'params': {
                                            'quote': '{{ testimonial_3_quote }}',
                                            'author': '{{ testimonial_3_author }}',
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
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 6,
                    'params': {
                        'content': '<h2>Ready to Begin Your Journey?</h2><p>Taking the first step toward therapy can feel daunting, but you don\'t have to navigate this journey alone. I offer a free 15-minute consultation to help you feel comfortable and see if we\'re a good fit.</p>'
                    },
                    'children': []
                },
                {
                    'type': 'row',
                    'placement_key': 'main',
                    'sort_order': 7,
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
                            'params': {'text': 'View Services', 'url': '/counseling', 'style': 'primary'},
                            'children': []
                        },
                        {
                            'type': 'button',
                            'placement_key': 'column',
                            'sort_order': 1,
                            'params': {'text': 'Free 15-min Consult', 'url': 'tel:{{ phone }}', 'style': 'secondary'},
                            'children': []
                        }
                    ]
                }
            ]
        },
        {
            'slug': '/counseling',
            'title': 'Counseling Services',
            'layout': 'single',
            'description': 'Explore our counseling services and treatment modalities',
            'blocks': [
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 0,
                    'params': {
                        'content': '<h1>Counseling Services</h1><p class="text-feature">{{ services_intro }}</p><p><strong>Healing • Transformation • Growth</strong></p>'
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 1,
                    'params': {
                        'content': '<h2>What I Specialize In</h2>'
                    },
                    'children': []
                },
                {
                    'type': 'flip_cards',
                    'placement_key': 'main',
                    'sort_order': 2,
                    'params': {
                        'columns': 3,
                        'cards': [
                            {'front_title': 'Trauma & PTSD', 'front_icon': '', 'back_description': 'Healing from sexual abuse, accidents, complex trauma, and distressing past events using evidence-based approaches.', 'back_cta_text': '', 'back_cta_url': ''},
                            {'front_title': 'Depression', 'front_icon': '', 'back_description': 'Finding hope and healing from persistent sadness, loss of interest, and the heavy weight of depression.', 'back_cta_text': '', 'back_cta_url': ''},
                            {'front_title': 'Anxiety and Panic', 'front_icon': '', 'back_description': 'Learning to manage overwhelming worry, panic attacks, and fear to reclaim a sense of calm and control.', 'back_cta_text': '', 'back_cta_url': ''},
                            {'front_title': 'Grief & Loss', 'front_icon': '', 'back_description': 'Processing the death of loved ones, loss of health, or ending of relationships in a supportive space.', 'back_cta_text': '', 'back_cta_url': ''},
                            {'front_title': 'Life Transitions', 'front_icon': '', 'back_description': 'Adjusting to divorce, career changes, empty nesting, and other major life shifts with resilience and clarity.', 'back_cta_text': '', 'back_cta_url': ''},
                            {'front_title': 'Relationship Problems', 'front_icon': '', 'back_description': 'Healing communication struggles, conflict, betrayal trauma, and rebuilding trust and intimacy.', 'back_cta_text': '', 'back_cta_url': ''}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 3,
                    'params': {
                        'content': '<h2>Treatment Modalities</h2>'
                    },
                    'children': []
                },
                {
                    'type': 'accordion',
                    'placement_key': 'main',
                    'sort_order': 4,
                    'params': {
                        'allow_multiple': False,
                        'items': [
                            {'title': 'EMDR', 'content': 'A research-backed therapy that facilitates the processing of traumatic memories through bilateral stimulation, reducing their lingering emotional charge.'},
                            {'title': 'Acceptance & Commitment Therapy (ACT)', 'content': 'Combines mindfulness skills with the practice of self-acceptance, encouraging psychological flexibility and commitment to personal values.'},
                            {'title': 'Cognitive Behavioral Therapy (CBT)', 'content': 'A structured type of talk therapy focused on developing practical skills to manage everyday challenges by changing negative thought patterns.'},
                            {'title': 'Dialectical Behavioral Therapy (DBT)', 'content': 'A cognitive-behavioral approach that emphasizes the psychosocial aspects of treatment, teaching skills to manage emotions and improve relationships.'},
                            {'title': 'Attachment Based Therapies', 'content': 'Explores how early life experiences and attachment styles influence current relationships and emotional patterns.'},
                            {'title': 'IFS or Parts Work', 'content': 'Views the mind as a system of various "parts," helping to heal wounded parts and restore leadership to the core Self.'}
                        ]
                    },
                    'children': []
                },
                {
                    'type': 'text',
                    'placement_key': 'main',
                    'sort_order': 5,
                    'params': {
                        'content': '<h2>Ready to Begin Your Healing Journey?</h2><p>Taking the first step toward therapy can feel daunting, but you don\'t have to navigate this alone. I offer a <strong>free 15-minute consultation</strong> to answer your questions and ensure you feel supported from the very start.</p>'
                    },
                    'children': []
                },
                {
                    'type': 'row',
                    'placement_key': 'main',
                    'sort_order': 6,
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
                            'params': {'text': 'Free 15-min Consult', 'url': 'tel:{{ phone }}', 'style': 'primary'},
                            'children': []
                        },
                        {
                            'type': 'button',
                            'placement_key': 'column',
                            'sort_order': 1,
                            'params': {'text': 'Back to Home', 'url': '/', 'style': 'secondary'},
                            'children': []
                        }
                    ]
                }
            ]
        }
    ],
    'global_blocks': [
        {
            'type': 'brand_logo',
            'placement_key': 'header',
            'sort_order': 0,
            'params': {
                'brand_name': '{{ business_name }}',
                'logo_image': '',
                'tagline': '{{ tagline_short }}',
                'link_url': '/'
            },
            'children': []
        },
        {
            'type': 'menu',
            'placement_key': 'header',
            'sort_order': 1,
            'params': {
                'items': [
                    {'label': 'Home', 'url': '/', 'type': 'link'},
                    {'label': 'Services', 'url': '/counseling', 'type': 'link'},
                    {'label': 'About', 'url': '/about', 'type': 'link'},
                    {'label': 'Contact', 'url': '#contact', 'type': 'link'}
                ],
                'style': 'default',
                'responsive': True,
                'hamburgerDirection': 'dropdown'
            },
            'children': []
        },
        {
            'type': 'social_links',
            'placement_key': 'footer',
            'sort_order': 0,
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
            'sort_order': 1,
            'params': {
                'content': '<p>© 2025 {{ business_name }}</p>'
            },
            'children': []
        }
    ]
}

# Placeholder schema for LLM content filling
CAIRNS_PLACEHOLDER_SCHEMA = {
    'business_name': {'type': 'text', 'description': 'Name of the therapy practice'},
    'tagline': {'type': 'text', 'description': 'Main tagline (e.g., "Healing • Transformation • Growth")'},
    'tagline_short': {'type': 'text', 'description': 'Short tagline for header'},
    'about_approach': {'type': 'richtext', 'description': 'Description of therapeutic approach'},
    'treatment_philosophy': {'type': 'richtext', 'description': 'Treatment philosophy description'},
    'services_intro': {'type': 'richtext', 'description': 'Introduction text for the Services page'},
    'testimonial_1_quote': {'type': 'text', 'description': 'First testimonial quote'},
    'testimonial_1_author': {'type': 'text', 'description': 'First testimonial author (first name + last initial)'},
    'testimonial_2_quote': {'type': 'text', 'description': 'Second testimonial quote'},
    'testimonial_2_author': {'type': 'text', 'description': 'Second testimonial author'},
    'testimonial_3_quote': {'type': 'text', 'description': 'Third testimonial quote'},
    'testimonial_3_author': {'type': 'text', 'description': 'Third testimonial author'},
    'phone': {'type': 'text', 'description': 'Contact phone number'},
    'facebook_url': {'type': 'url', 'description': 'Facebook page URL'},
    'instagram_url': {'type': 'url', 'description': 'Instagram profile URL'}
}


class Command(BaseCommand):
    help = 'Create the Cairns Counseling site template in the database'

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
            base_css = get_cairns_css()
            logo_url = get_cairns_logo()
            self.stdout.write(self.style.SUCCESS(f'Extracted CSS and logo: {logo_url}'))
        else:
            base_css = CAIRNS_CSS_FALLBACK
            logo_url = None
        
        template, created = SiteTemplate.objects.update_or_create(
            slug='cairns-counseling',
            defaults={
                'name': "Therapist / Counseling",
                'description': 'A calming, professional template for therapists, counselors, and mental health practitioners. Features hero section, approach overview, treatment philosophy pillars, testimonials carousel, and clear CTAs.',
                'tags': ['therapist', 'counseling', 'healthcare', 'mental-health', 'wellness'],
                'base_css': base_css,
                'pages_json': CAIRNS_PAGES_JSON,
                'placeholder_schema': CAIRNS_PLACEHOLDER_SCHEMA,
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
