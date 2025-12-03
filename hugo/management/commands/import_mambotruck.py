from django.core.management.base import BaseCommand
from django.db import transaction
from hugo.models import Page, BlockDefinition, BlockInstance, LayoutTemplate, Website
import uuid


class Command(BaseCommand):
    help = 'Import MamboTruck food truck template with block definitions and example content'

    def handle(self, *args, **options):
        self.stdout.write('Importing MamboTruck Template...')
        
        with transaction.atomic():
            # Create block definitions for MamboTruck template
            self.create_block_definitions()
            
            self.stdout.write(self.style.SUCCESS('✓ Block definitions created'))
            
        self.stdout.write(self.style.SUCCESS('✓ MamboTruck template imported successfully!'))
        self.stdout.write('To create a website using this template, add blocks manually in the CMS editor')

    def create_block_definitions(self):
        """Create all necessary block definitions for MamboTruck template"""
        
        definitions = [
            {
                'id': 'cta_hero',
                'label': 'CTA Hero',
                'icon': 'layout',
                'has_visual_preview': False,
                'default_params': {
                    'headline': 'Food Truck Catering for Events Everyone Will Remember',
                    'subheadline': 'Say goodbye to boring catering and overwhelming planning',
                    'cta_text': 'BOOK THE TRUCK',
                    'cta_url': '/packages',
                    'background_image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=1200&q=80'
                }
            },
            {
                'id': 'features_grid',
                'label': 'Features Grid',
                'icon': 'columns',
                'has_visual_preview': False,
                'default_params': {
                    'title': 'Why Choose Us',
                    'features': [
                        {
                            'icon': 'check',
                            'title': 'Reliable Service',
                            'description': 'Dependable scheduling and clear communication ensure your catering is one less thing to worry about.'
                        },
                        {
                            'icon': 'check',
                            'title': 'Interactive Food Truck Experience',
                            'description': 'The food truck itself is a fun, engaging centerpiece for your event, adding personality and flair.'
                        },
                        {
                            'icon': 'check',
                            'title': 'Transparent Pricing',
                            'description': 'Clear, upfront pricing eliminates unexpected costs and ensures you can plan confidently within your budget.'
                        }
                    ]
                }
            },
            {
                'id': 'process_steps',
                'label': 'Process Steps',
                'icon': 'layout',
                'has_visual_preview': False,
                'default_params': {
                    'title': "Here's how it works:",
                    'steps': [
                        {
                            'title': 'Book Your Catering Experience',
                            'description': 'Pick your ideal package or request a custom option, confirm your date, and provide us with the event details.'
                        },
                        {
                            'title': 'Stay Connected as We Prepare',
                            'description': 'Our team not only preps every detail, but we also keep you updated with our seamless communication system.'
                        },
                        {
                            'title': 'Savor the Celebration',
                            'description': "When the day arrives, our truck rolls in to serve your guests with vibrant Cuban fusion cuisine."
                        }
                    ]
                }
            },
            {
                'id': 'stats_counter',
                'label': 'Stats Counter',
                'icon': 'layout',
                'has_visual_preview': False,
                'default_params': {
                    'stats': [
                        {'value': '35', 'suffix': 'k+', 'label': 'Cuban meals Served'},
                        {'value': '2', 'suffix': 'k+', 'label': 'Happy Clients'},
                        {'value': '5', 'suffix': '+', 'label': 'Years Of Experience'}
                    ]
                }
            },
            {
                'id': 'menu_grid',
                'label': 'Menu Grid',
                'icon': 'image',
                'has_visual_preview': False,
                'default_params': {
                    'title': 'Our Menu Favorites',
                    'items': [
                        {
                            'name': 'Cari-Bowl',
                            'image': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80',
                            'description': 'Caribbean flavors in a bowl'
                        },
                        {
                            'name': 'Cuban Sandwich',
                            'image': 'https://images.unsplash.com/photo-1509722747041-616f39b57569?w=400&q=80',
                            'description': 'Traditional pressed sandwich'
                        },
                        {
                            'name': 'Supreme Nachos',
                            'image': 'https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=400&q=80',
                            'description': 'Loaded with toppings'
                        },
                        {
                            'name': 'Mambo BBQ Sandwich',
                            'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&q=80',
                            'description': 'Smoky BBQ goodness'
                        }
                    ]
                }
            },
            {
                'id': 'social_links',
                'label': 'Social Media Links',
                'icon': 'layout',
                'has_visual_preview': False,
                'default_params': {
                    'links': [
                        {'platform': 'facebook', 'url': 'https://facebook.com/mambotruck'},
                        {'platform': 'instagram', 'url': 'https://instagram.com/mambotruck'},
                        {'platform': 'twitter', 'url': 'https://twitter.com/mambotruck'}
                    ]
                }
            },
            {
                'id': 'faq',
                'label': 'FAQ',
                'icon': 'help-circle',
                'has_visual_preview': False,
                'default_params': {
                    'title': 'Frequently Asked Questions',
                    'questions': [
                        {
                            'question': 'How far in advance should I book?',
                            'answer': 'We recommend booking at least 2-3 weeks in advance, especially for weekends and peak seasons.'
                        },
                        {
                            'question': 'What is included in the catering package?',
                            'answer': 'Our packages include the food truck, staff, serving equipment, and cleanup. Food and beverages are customized based on your selections.'
                        },
                        {
                            'question': 'Do you accommodate dietary restrictions?',
                            'answer': 'Absolutely! We can accommodate vegetarian, vegan, gluten-free, and other dietary needs. Just let us know when booking.'
                        }
                    ]
                }
            },
            {
                'id': 'google_reviews',
                'label': 'Google Reviews',
                'icon': 'star',
                'has_visual_preview': False,
                'default_params': {
                    'title': 'What Our Customers Say',
                    'subtitle': 'We take pride in serving delicious food and creating memorable experiences.',
                    'reviews': [
                        {
                            'name': 'Sarah Johnson',
                            'rating': 5,
                            'text': 'The food was absolutely amazing! Everyone at our wedding raved about the Cuban sandwiches. Highly recommend!',
                            'date': '2 weeks ago',
                            'image': ''
                        },
                        {
                            'name': 'Mike Chen',
                            'rating': 5,
                            'text': 'Best food truck in town. The service was professional and the setup looked great. Will definitely book again.',
                            'date': '1 month ago',
                            'image': ''
                        },
                        {
                            'name': 'Emily Davis',
                            'rating': 4,
                            'text': 'Great food and friendly staff. The portions were generous and everything tasted fresh.',
                            'date': '2 months ago',
                            'image': ''
                        }
                    ]
                }
            }
        ]
        
        for def_data in definitions:
            BlockDefinition.objects.update_or_create(
                id=def_data['id'],
                defaults={
                    'label': def_data['label'],
                    'icon': def_data['icon'],
                    'has_visual_preview': def_data['has_visual_preview'],
                    'default_params': def_data['default_params']
                }
            )
