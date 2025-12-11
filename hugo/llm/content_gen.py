import json
import os
from typing import Dict, List, Optional
from hugo.schemas import BusinessProfile
from hugo.llm.providers import get_provider

def generate_site_copy(profile: BusinessProfile, requirements: List[str] = None) -> Dict:
    """
    Generates marketing copy for the website based on the business profile.
    
    Args:
        profile: The scraped BusinessProfile data
        requirements: List of content keys needed (e.g. ['features', 'hero_headline'])
        
    Returns:
        Dict containing the generated content
    """
    # Defaults
    if not requirements:
        requirements = ["features_grid", "hero_headline", "hero_subheadline"]
    
    provider = get_provider()
    
    if provider:
        try:
            return _generate_with_llm(provider, profile, requirements)
        except Exception as e:
            print(f"[LLM] Error using provider: {e}. Falling back to mock.")
    else:
        print("[LLM] No provider available. Using mock generation.")
    
    return _mock_generation(profile, requirements)

def _generate_with_llm(provider, profile, requirements) -> Dict:
    system_prompt = (
        "You are an expert copywriter for business websites. "
        "Your goal is to synthesize structured marketing content from raw business profile data."
    )
    
    user_prompt = f"""
    Please generate website content for the following business:
    
    Name: {profile.name}
    Tagline: {profile.tagline}
    Description: {profile.description}
    Reviews (Sample): {str([r.text for r in profile.reviews[:3]]) if profile.reviews else "None"}
    
    Requirements:
    Generate a valid JSON object where each key corresponds to a requirement.
    For each item, providing an object with:
    - "content": The generated content (string, list, or object as requested below)
    - "confidence_score": A float between 0.0 (total guess) and 1.0 (fully supported by data)
    
    Keys to generate: {requirements}
    
    Specific Instructions:
    - 'features_grid': content should be a list of 3 items (title, description).
    - 'hero_headline': content should be a string. STRICT LIMIT: Maximum 10 words. Use a punchy phrase like "Best Chicken in Utah".
    - 'about_content': content should be a string (approx 50 words).
    - 'menu_items': content should be a list of objects, each with 'name', 'description', 'price' (string). Infer from reviews/description. Estimate prices if unsure (e.g. "$10-15").
    - 'catering_faq': content should be a list of 4 FAQs. Only generate answers if you are confident based on the profile (or common industry knowledge). If not confident about specific constraints (like power/minimums), generic safe answers are okay but lower the confidence score.
    """
    
    raw_response = provider.generate_json(system_prompt, user_prompt)
    
    # Filter based on confidence
    filtered_content = {}
    
    try:
        threshold = float(os.environ.get("LLM_CONFIDENCE_THRESHOLD", "0.6"))
    except ValueError:
        threshold = 0.6
    
    for key, value in raw_response.items():
        if isinstance(value, dict) and 'confidence_score' in value:
            score = value['confidence_score']
            content = value.get('content')
            
            if score >= threshold:
                filtered_content[key] = content
            else:
                print(f"[LLM] Dropped '{key}' due to low confidence ({score})")
        else:
            # Handle legacy/malformed response by accepting it (or drop? accept for robustness)
            filtered_content[key] = value
            
    return filtered_content


def _mock_generation(profile: BusinessProfile, requirements: List[str]) -> Dict:
    """Fallback generator using heuristics/hardcoded templates"""
    
    # Mocking high confidence for core items, low for tricky ones
    
    content = {}
    
    # ... (Features Grid logic exists)
    
    features = []
    # Feature 1: Food Quality
    features.append({
        "title": "Fresh & Made to Order",
        "description": f"Experience the taste of fresh, never frozen {profile.categories[0] if profile.categories else 'food'}, prepared right when you order."
    })
    
    # Feature 2: Convenience/Service
    features.append({
        "title": "Fast & Friendly",
        "description": "We bring the flavor to you! Perfect for quick lunches, events, and catering needs."
    })
    
    # Feature 3: Rating/Trust
    rating = profile.stats.get('rating')
    if rating and rating >= 4.0:
        features.append({
            "title": "Top Rated Local Eats",
            "description": f"Join our community of happy customers. We're proud to serve our local area with high-quality eats."
        })
    else:
         features.append({
            "title": "Local Favorite",
            "description": "A staple of the local food scene, serving up delicious bites for everyone to enjoy."
        })

    content['features_grid'] = features
    
    # 2. Hero Headline
    headline = profile.tagline
    if headline and len(headline) > 60:
        headline = f"Delicious {profile.name}"
    content['hero_headline'] = headline or f"Delicious {profile.name}"
    content['hero_subheadline'] = profile.description or "Serving the best food in town."
    
    # About
    content['about_content'] = (
        f"At {profile.name}, we are passionate about bringing the best street food to you. "
        f"{profile.description or 'We specialize in delicious, fresh meals.'} "
        "Whether you're grabbing a quick lunch or planning an event, we're here to serve you."
    )
    
    # Catering FAQ - Mocking a scenario where we might NOT know
    # If explicit data missing, maybe we shouldn't guess?
    # For mock, we'll return it but arguably this is where 'confidence' matters.
    content['catering_faq'] = [
        {"question": "Do you travel for private events?", "answer": "Yes! We love bringing our truck to weddings, parties, and corporate events."},
        {"question": "What is the minimum spend?", "answer": "Our minimums vary by location and date. Please contact us for a custom quote."},
        {"question": "Do I need to provide power?", "answer": "We are fully self-sufficient with our own generator."},
        {"question": "How far in advance should I book?", "answer": "We recommend booking at least 2-3 months in advance."}
    ]
    
    if 'menu_items' in requirements:
         content['menu_items'] = [
            {"name": "Famous Chicken Strips", "description": "Crispy, golden-brown chicken tenders served with our signature house sauce.", "price": "$12.99"},
            {"name": "Hand-Cut Fries", "description": "Freshly cut potatoes, twice-fried for extra crispiness.", "price": "$5.99"},
            {"name": "Combo Meal", "description": "3 strips, fries, and a drink.", "price": "$16.99"},
            {"name": "Spicy Dippin Sauce", "description": "Our secret blend of spices and creaminess.", "price": "$0.50"}
         ]

    return content
