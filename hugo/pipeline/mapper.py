"""
Content Mapper

Maps BusinessProfile data to template block parameters.
Each template may have its own mapping strategy.
"""
from typing import Dict, Any, List
from hugo.schemas import BusinessProfile


def map_profile_to_blocks(profile: BusinessProfile, template_slug: str) -> Dict[str, Any]:
    """
    Generate block parameter overrides based on profile and template.
    
    Returns dict with structure:
    {
        'pages': {
            '/': {
                'hero': { params... },
                'text': { params... },
            },
            '/menu': {
                'menu_grid': { params... }
            }
        },
        'global': {
            'footer': { params... },
            'social_links': { params... }
        },
        'css': '...'
    }
    """
    # Get template-specific mapper
    if template_slug == 'food-truck-v2':
        return _map_food_truck_v2(profile)
    elif template_slug == 'therapy-v1':
        return _map_therapy_v1(profile)
    else:
        # Generic fallback
        return _map_generic(profile)


def _map_food_truck_v2(profile: BusinessProfile) -> Dict[str, Any]:
    """Mapper for food-truck-v2 template."""
    
    # Hero block
    hero_params = {
        'headline': profile.name,
        'subheadline': profile.tagline or f"Serving {profile.location_str}" if profile.location_str else '',
        'image': profile.hero_image_local_path or profile.hero_image_url,
        'cta_text': 'View Menu',
        'cta_link': '/menu'
    }
    
    # Story/About block
    story_params = {
        'content': f"<h2>Our Story</h2><p>{profile.description}</p>" if profile.description else ''
    }
    
    # Menu grid
    menu_items = []
    for item in profile.menu_items:
        menu_items.append({
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'image': item.image_url
        })
    menu_params = {'items': menu_items}
    
    # Reviews
    reviews = []
    for review in profile.reviews:
        reviews.append({
            'author': review.author,
            'rating': review.rating,
            'text': review.text,
            'date': review.date
        })
    reviews_params = {'reviews': reviews}
    
    # Social links
    social_links = []
    for link in profile.social_links:
        social_links.append({
            'platform': link.platform,
            'url': link.url
        })
    social_params = {'links': social_links}
    
    # Footer
    footer_content = f"<p><strong>{profile.name}</strong><br>"
    if profile.location_str:
        footer_content += f"{profile.location_str}<br>"
    if profile.phone:
        footer_content += f"{profile.phone}<br>"
    footer_content += "Follow us for daily updates!</p>"
    footer_params = {'content': footer_content}
    
    return {
        'pages': {
            '/': {
                'hero': hero_params,
                'text': story_params,
                'reviews_carousel': reviews_params,
            },
            '/menu': {
                'menu_grid': menu_params
            }
        },
        'global': {
            'footer': footer_params,
            'social_links': social_params
        },
        'css': profile.colors_css
    }


def _map_therapy_v1(profile: BusinessProfile) -> Dict[str, Any]:
    """Mapper for therapy-v1 template (placeholder)."""
    # Similar structure but with therapy-specific blocks
    hero_params = {
        'headline': profile.name,
        'subheadline': profile.tagline,
        'image': profile.hero_image_local_path or profile.hero_image_url,
        'cta_text': 'Book Appointment',
        'cta_link': profile.booking_url or '/contact'
    }
    
    return {
        'pages': {
            '/': {
                'hero': hero_params,
                'text': {'content': f"<h2>About</h2><p>{profile.description}</p>"}
            }
        },
        'global': {},
        'css': profile.colors_css
    }


def _map_generic(profile: BusinessProfile) -> Dict[str, Any]:
    """Generic mapper for unknown templates."""
    return {
        'pages': {
            '/': {
                'hero': {
                    'headline': profile.name,
                    'subheadline': profile.tagline,
                    'image': profile.hero_image_local_path or profile.hero_image_url
                }
            }
        },
        'global': {},
        'css': profile.colors_css
    }
