#!/usr/bin/env python
"""
Create Strippin Dippin Chicken website from Food Truck V2 template
with extracted content from Yelp and Food Truck League
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import Website
from hugo.template_service import create_website_from_template

# Extracted data from Yelp and Food Truck League
BUSINESS_DATA = {
    # Business Identity
    'business_name': 'Strippin Dippin Chicken',
    'brand_logo_url': '',  # Missing - needs to be provided
    
    # Hero Section
    'hero_title': 'Fresh Chicken Strips & Hand-Cut Fries',
    'hero_subtitle': 'Made-to-order chicken tenders with house-made dipping sauces',
    'hero_bg_image': '',  # Missing
    'hero_cta_text': 'Find Us Today',
    'hero_cta_url': '#locations',
    
    # Value Propositions
    'value_props_title': 'Why Choose Strippin Dippin Chicken',
    'value_props_intro': 'Everything we serve is made fresh to order, right in front of you',
    'value_propositions': [
        {
            'title': 'Fresh & Made to Order',
            'description': 'We prepare every single order fresh - cutting potatoes and battering chicken right on the truck',
            'icon': 'chef-hat'
        },
        {
            'title': 'Hand-Cut Fries',
            'description': 'Our fries are cut fresh from whole potatoes for each order, perfectly salted and crispy',
            'icon': 'utensils'
        },
        {
            'title': 'House-Made Sauces',
            'description': "All our sauces are Jerremy's own recipes, including our famous black peppercorn ranch",
            'icon': 'droplet'
        }
    ],
    
    # Menu Section
    'menu_section_title': 'Our Menu',
    'menu_intro_text': 'Fresh chicken strips, hand-cut French fries, and awesome hand-made dipping sauces.',
    'menu_items': [
        {
            'name': '2-Piece Chicken Tender Meal',
            'description': 'Two fresh chicken tenders with hand-cut fries and your choice of sauce',
            'price': '$8.99',
            'image': ''
        },
        {
            'name': '3-Piece Chicken Tender Meal',
            'description': 'Three fresh chicken tenders with hand-cut fries and your choice of sauce',
            'price': '$10.99',
            'image': ''
        },
        {
            'name': 'Chicken Salad',
            'description': 'Fresh lettuce with crispy chicken tenders, veggies, and your choice of dressing',
            'price': '$9.99',
            'image': ''
        },
        {
            'name': 'Hand-Cut Fries',
            'description': 'Freshly cut potatoes fried to perfection, perfectly salted',
            'price': '$4.99',
            'image': ''
        }
    ],
    'menu_cta_text': 'View Full Menu',
    'menu_cta_url': '/menu',
    
    # Locations & Schedule
    'locations_title': 'Find Us',
    'locations_description': '<p>We travel all around the West Jordan area and beyond. Follow us on Instagram and Facebook to see where we\'ll be next!</p>',
    'find_us_steps': [
        {
            'title': 'Follow Us on Social Media',
            'description': 'Check Instagram and Facebook for our daily schedule and location updates'
        },
        {
            'title': 'Look for Our Truck',
            'description': 'We serve across North, South, East, and West areas of the Salt Lake Valley'
        },
        {
            'title': 'Place Your Order',
            'description': 'Watch as we prepare your food fresh - cutting fries and battering chicken right in front of you!'
        }
    ],
    'locations_embed_code': '',  # Missing - social media feed or map
    
    # Catering
    'catering_title': 'Catering & Events',
    'catering_description': 'We\'re super fast with catering and large events. Book Strippin Dippin Chicken for your next corporate lunch, birthday party, wedding, or special event!',
    'catering_cta_text': 'Book Catering',
    'catering_cta_url': '/catering',
    'catering_faqs': [
        {
            'title': 'What events do you cater?',
            'content': '<p>We cater all types of events including corporate lunches, birthday parties, weddings, festivals, and private events.</p>'
        },
        {
            'title': 'How far in advance should I book?',
            'content': '<p>We recommend booking at least 2 weeks in advance for large events, though we can sometimes accommodate last-minute requests.</p>'
        },
        {
            'title': 'What is your minimum for catering?',
            'content': '<p>Our minimum varies by event type and location. Contact us for a custom quote!</p>'
        }
    ],
    
    # About/Story
    'about_title': 'Our Story',
    'about_story': '''<p>Jerremy and Ashley, a husband and wife team, started their food truck journey together in the fall of 2021. After owning a fencing installation business for 5 years, they decided to pursue Jerremy's dream of serving great food.</p>
    
<p>After visiting many food trucks over the years, they knew they wanted to serve food that was super fresh and prepped right on the truck. They developed their chicken and fries concept, ensuring the freshest chicken tenders and fresh-cut potatoes for their fries - cut right on the truck for each order.</p>

<p>The bonus? They make all their own house-made sauces using Jerremy's own recipes. They're super fast with catering and large events, and Ashley's personality while taking orders is top-notch, bringing back many repeat customers - she'll probably even remember your usual order!</p>''',
    'about_image_url': '',  # Missing
    'about_image_alt': 'Jerremy and Ashley at their food truck',
    'founder_quote': 'All the sauces are my own recipes, and we hope you enjoy what we love to do.',
    'founder_name': 'Jerremy',
    'founder_title': 'Co-Owner & Chef',
    
    # Testimonials & Reviews (from Yelp)
    'testimonials_title': 'What Our Customers Say',
    'testimonial_slides': [],  # Will use google_reviews instead
    'google_reviews': [
        {
            'name': 'James O.',
            'rating': 5,
            'text': 'Great food!! Great price, Awesome value!! Will even cater for your events. No better chicken!!',
            'date': 'November 2025'
        },
        {
            'name': 'Oscar Z.',
            'rating': 5,
            'text': 'These guys came to my office and indulged me with a great lunch meal. The hand cut potatoes and the size of the strips left me fully satisfied. The person taking my order and payment was helpful and friendly, and the quality of the food talked for the care with which it was cooked.',
            'date': 'January 2025'
        },
        {
            'name': 'Luna D.',
            'rating': 5,
            'text': 'I had the chicken salad and my daughter had the 2 piece strips. The fries were perfectly salted, the chicken was crispy, and the sauces were amazing. The bbq and peppercorn ranch mix on the chicken salad was amazing, and the lettuce was very fresh.',
            'date': 'February 2025'
        },
        {
            'name': 'John C.',
            'rating': 5,
            'text': 'This food truck was amazing! They make everything from scratch per order. They actually cut the potatoes right in front of you and dip the chicken in the batter and fry it right in front of you. This puts the food truck for chicken at a new level.',
            'date': 'August 2021'
        },
        {
            'name': 'Keisha F.',
            'rating': 4,
            'text': 'First things first, the ranch is amazing. It\'s a black peppercorn ranch and just phenomenal. Fries are great too. The flavor is 100% on point. All in all, the flavors are on point and the fact that it\'s all made to order is really awesome!',
            'date': 'August 2021'
        }
    ],
    
    # Stats
    'stats': [
        {
            'value': '3',
            'label': 'Years Serving',
            'suffix': '+'
        },
        {
            'value': '100',
            'label': 'Events Catered',
            'suffix': '%'
        },
        {
            'value': '5',
            'label': 'House-Made Sauces',
            'suffix': ''
        }
    ],
    
    # Final CTA
    'final_cta_title': 'Ready to Try the Best Chicken Tenders?',
    'final_cta_subtitle': 'Follow us on social media to find out where we\'ll be next, or book us for your event!',
    'cta_primary_text': 'Follow on Instagram',
    'cta_primary_url': 'https://www.instagram.com/strippindippinchicken/',
    'cta_secondary_text': 'Book Catering',
    'cta_secondary_url': '/catering',
    
    # Footer
    'footer_copyright': '© 2024 Strippin Dippin Chicken. All rights reserved.',
    'footer_tagline': 'Fresh chicken, hand-cut fries, homemade sauces.',
    'social_links': [
        {
            'platform': 'instagram',
            'url': 'https://www.instagram.com/strippindippinchicken/'
        },
        {
            'platform': 'facebook',
            'url': '#'  # Not provided
        },
        {
            'platform': 'yelp',
            'url': 'https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan'
        }
    ],
    
    # Menu Page
    'menu_page_hero_title': 'Our Full Menu',
    'menu_page_hero_subtitle': 'Fresh chicken tenders, hand-cut fries, and house-made sauces',
    'menu_page_bg_image': '',
    'menu_page_section_title': 'Choose Your Meal',
    'full_menu_items': [
        {
            'name': '2-Piece Chicken Tender Meal',
            'description': 'Two fresh chicken tenders with hand-cut fries and your choice of sauce',
            'price': '$8.99',
            'image': ''
        },
        {
            'name': '3-Piece Chicken Tender Meal',
            'description': 'Three fresh chicken tenders with hand-cut fries and your choice of sauce',
            'price': '$10.99',
            'image': ''
        },
        {
            'name': 'Chicken Salad',
            'description': 'Fresh lettuce with crispy chicken tenders, veggies, and your choice of dressing',
            'price': '$9.99',
            'image': ''
        },
        {
            'name': 'Hand-Cut Fries',
            'description': 'Freshly cut potatoes fried to perfection',
            'price': '$4.99',
            'image': ''
        },
        {
            'name': 'Black Peppercorn Ranch',
            'description': 'Our famous house-made ranch sauce',
            'price': '$0.50',
            'image': ''
        },
        {
            'name': 'BBQ Sauce',
            'description': 'House-made BBQ sauce',
            'price': '$0.50',
            'image': ''
        },
        {
            'name': 'Honey Mustard',
            'description': 'Sweet and tangy honey mustard',
            'price': '$0.50',
            'image': ''
        }
    ],
    'menu_photos_slides': [],  # Missing - no photos available
    
    # Catering Page
    'catering_page_hero_title': 'Catering Services',
    'catering_page_hero_subtitle': 'Book us for your next event!',
    'catering_page_bg_image': '',
    'catering_page_intro_title': 'Fresh Food for Your Event',
    'catering_page_intro_text': '<p>We\'re super fast with catering and large events. Book Strippin Dippin Chicken for fresh, made-to-order chicken tenders and hand-cut fries at your next event!</p>',
    'catering_event_types': [
        {
            'title': 'Corporate Events',
            'description': 'Perfect for office lunches, team building events, and corporate gatherings',
            'icon': 'briefcase'
        },
        {
            'title': 'Private Parties',
            'description': 'Birthday parties, graduations, and family celebrations',
            'icon': 'party-popper'
        },
        {
            'title': 'Weddings & Special Events',
            'description': 'Make your special day delicious with fresh, quality food',
            'icon': 'heart'
        }
    ],
    'catering_process_title': 'How It Works',
    'catering_process_steps': [
        {
            'title': 'Contact Us',
            'description': 'Reach out via phone, email, or social media with your event details'
        },
        {
            'title': 'Get a Quote',
            'description': 'We\'ll provide a custom quote based on your guest count and preferences'
        },
        {
            'title': 'Book Your Event',
            'description': 'Confirm your booking and we\'ll handle the rest!'
        },
        {
            'title': 'Enjoy Fresh Food',
            'description': 'We\'ll arrive on time and serve fresh, made-to-order food at your event'
        }
    ],
    'catering_faq_title': 'Catering FAQ',
    'catering_page_faqs': [
        {
            'title': 'What events do you cater?',
            'content': '<p>We cater all types of events including corporate lunches, birthday parties, weddings, festivals, and private events.</p>'
        },
        {
            'title': 'How far in advance should I book?',
            'content': '<p>We recommend booking at least 2 weeks in advance for large events, though we can sometimes accommodate last-minute requests.</p>'
        },
        {
            'title': 'What is your minimum for catering?',
            'content': '<p>Our minimum varies by event type and location. Contact us for a custom quote!</p>'
        },
        {
            'title': 'Do you provide serving staff?',
            'content': '<p>Yes! Ashley and Jerremy will be there serving your guests with friendly, personalized service.</p>'
        }
    ],
    'catering_contact_title': 'Ready to Book?',
    'catering_contact_text': 'Contact us today to discuss your event and get a custom quote!',
    'catering_contact_button': 'Contact Us',
    
    # Contact Page
    'contact_page_heading': 'Get in Touch',
    'contact_page_instructions': '<p>Have questions or want to book us for your event? Reach out through any of the methods below!</p>',
    'contact_methods_title': 'Contact Methods',
    'contact_methods_list': '''
- **Instagram**: [@strippindippinchicken](https://www.instagram.com/strippindippinchicken/)
- **Yelp**: [Leave us a review](https://www.yelp.com/biz/strippin-dippin-chicken-west-jordan)
- **Email**: Contact us through social media
    ''',
    'contact_hours_title': 'When to Find Us',
    'contact_hours_info': '''
**Follow us on social media for our daily schedule!**

We travel throughout the Salt Lake Valley serving fresh food at various locations. Check Instagram for today's location.
    '''
}


def main():
    """Create the Strippin Dippin Chicken website"""
    
    print("Creating Strippin Dippin Chicken website from Food Truck V2 template...")
    
    # Create website from template
    website = create_website_from_template(
        template_slug='food-truck-v2',
        website_name='Strippin Dippin Chicken',
        website_slug='strippin-dippin-chicken'
    )
    
    print(f"✓ Created website: {website.name} ({website.slug})")
    print(f"  Website ID: {website.id}")
    print(f"  Pages created: {website.pages.count()}")
    print(f"  Blocks created: {website.blocks.count()}")
    
    # TODO: Populate placeholder content
    # The template uses placeholders like {{business_name}}, {{hero_title}}, etc.
    # These need to be replaced in the block params
    # This will require iterating through all blocks and replacing placeholder strings
    
    print("\n✓ Website created successfully!")
    print(f"\nNote: Placeholder content has been extracted but needs to be applied.")
    print(f"The template uses placeholders that need to be replaced with actual content.")
    print(f"\nNext steps:")
    print(f"1. Manually update block params to replace placeholders")
    print(f"2. Add missing images (logo, hero background, menu photos)")
    print(f"3. Get exact prices and update menu")
    print(f"4. Add Facebook URL and other social links")
    
    return website


if __name__ == '__main__':
    website = main()
