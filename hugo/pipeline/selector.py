"""
Template Selector

Chooses the appropriate template based on profile categories or explicit choice.
"""
from typing import Optional, Dict, List
from hugo.schemas import BusinessProfile

# Registry mapping categories to template slugs
TEMPLATE_REGISTRY: Dict[str, str] = {
    # Food & Beverage
    'food truck': 'food-truck-v2',
    'food': 'food-truck-v2',
    'restaurant': 'food-truck-v2',
    'catering': 'food-truck-v2',
    'chicken': 'food-truck-v2',
    'taco': 'food-truck-v2',
    'pizza': 'food-truck-v2',
    
    # Healthcare
    'therapist': 'therapy-v1',
    'therapy': 'therapy-v1',
    'counseling': 'therapy-v1',
    'mental health': 'therapy-v1',
    'psychologist': 'therapy-v1',
    'counselor': 'therapy-v1',
    
    # Default
    'default': 'food-truck-v2'
}


def select_template(profile: BusinessProfile, explicit_choice: Optional[str] = None) -> str:
    """
    Select the best template for the profile.
    
    Args:
        profile: BusinessProfile with categories
        explicit_choice: If provided, use this template slug directly
    
    Returns:
        Template slug string
    """
    # Explicit choice takes priority
    if explicit_choice:
        print(f"[TemplateSelector] Using explicit choice: {explicit_choice}")
        return explicit_choice
    
    # Check categories against registry
    for category in profile.categories:
        category_lower = category.lower()
        
        # Direct match
        if category_lower in TEMPLATE_REGISTRY:
            template = TEMPLATE_REGISTRY[category_lower]
            print(f"[TemplateSelector] Matched '{category}' -> {template}")
            return template
        
        # Partial match
        for key, template in TEMPLATE_REGISTRY.items():
            if key in category_lower or category_lower in key:
                print(f"[TemplateSelector] Partial match '{category}' ~ '{key}' -> {template}")
                return template
    
    # Fallback to default
    default = TEMPLATE_REGISTRY['default']
    print(f"[TemplateSelector] No match, using default: {default}")
    return default


def get_available_templates() -> List[str]:
    """Return list of unique template slugs available."""
    return list(set(TEMPLATE_REGISTRY.values()))
