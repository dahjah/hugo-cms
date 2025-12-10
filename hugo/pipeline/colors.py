"""
Color Generator

Extracts color palette from profile images and applies to profile.
"""
import os
import requests
from hugo.schemas import BusinessProfile


def generate_colors(profile: BusinessProfile, media_root: str = 'media') -> BusinessProfile:
    """
    Generate color palette from profile image.
    Updates profile.colors_css and profile.hero_image_local_path.
    
    Args:
        profile: BusinessProfile to enhance
        media_root: Base directory for media storage
    
    Returns:
        Updated BusinessProfile
    """
    from hugo.utils.image_colors import extract_colors_from_path
    
    # Skip if colors already set
    if profile.colors_css:
        print("[ColorGenerator] Colors already set, skipping")
        return profile
    
    # Find image to extract from
    image_url = profile.hero_image_url or profile.logo_url
    if not image_url:
        print("[ColorGenerator] No image available for color extraction")
        return profile
    
    # Create media directory for this profile
    profile_media_dir = os.path.join(media_root, 'uploads', profile.slug)
    os.makedirs(profile_media_dir, exist_ok=True)
    
    # Download image
    try:
        ext = image_url.split('.')[-1].split('?')[0]
        if len(ext) > 4:
            ext = 'jpg'
        
        filename = f"brand_hero.{ext}"
        local_path = os.path.join(profile_media_dir, filename)
        
        if not os.path.exists(local_path):
            print(f"[ColorGenerator] Downloading {image_url}...")
            response = requests.get(image_url, timeout=20)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
            else:
                print(f"[ColorGenerator] Download failed: {response.status_code}")
                return profile
        else:
            print(f"[ColorGenerator] Using cached: {local_path}")
        
        # Extract colors
        print(f"[ColorGenerator] Extracting colors from {local_path}...")
        css = extract_colors_from_path(local_path)
        
        if css:
            profile.colors_css = css
            profile.hero_image_local_path = f"/media/uploads/{profile.slug}/{filename}"
            print("[ColorGenerator] ✓ Colors extracted successfully")
        
    except Exception as e:
        print(f"[ColorGenerator] Error: {e}")
    
    return profile
