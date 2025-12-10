"""
Instagram Scraper

Extends BaseScraper to provide Instagram profile extraction via HikerAPI.
"""
import json
from typing import ClassVar, Set

from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.schemas import BusinessProfile, SocialLink


class InstagramScraper(BaseScraper):
    """
    Scraper for Instagram profiles via HikerAPI.
    
    Supported fields:
        name (username), description (bio), logo_url (profile pic),
        gallery_images (recent posts), website_url (external link)
    """
    
    platform: ClassVar[str] = "instagram"
    
    supported_fields: ClassVar[Set[str]] = {
        'name', 'description', 'logo_url', 'hero_image_url',
        'gallery_images', 'website_url', 'stats'
    }
    
    # HikerAPI config
    API_KEY: ClassVar[str] = "1b42yowz11l52wmybh4x8e2ujp4kj49g"
    API_BASE: ClassVar[str] = "https://api.hikerapi.com"
    
    @classmethod
    def can_handle(cls, identifier: str) -> bool:
        """Check if this looks like an Instagram URL or username."""
        if not identifier:
            return False
        lower = identifier.lower()
        return 'instagram.com' in lower or identifier.startswith('@')
    
    @classmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Extract username and prepare API headers.
        """
        try:
            # Extract username
            if 'instagram.com/' in identifier:
                username = identifier.split('instagram.com/')[-1].strip('/').split('?')[0]
            elif identifier.startswith('@'):
                username = identifier[1:]
            else:
                username = identifier
            
            if not username or len(username) < 2:
                return ScraperContext(
                    identifier=identifier,
                    normalized_id='',
                    platform=cls.platform,
                    is_valid=False,
                    error="Invalid Instagram username"
                )
            
            return ScraperContext(
                identifier=identifier,
                normalized_id=username,
                platform=cls.platform,
                headers={"x-access-key": cls.API_KEY},
                api_key=cls.API_KEY,
                metadata={
                    'profile_url': f"https://instagram.com/{username}"
                }
            )
            
        except Exception as e:
            return ScraperContext(
                identifier=identifier,
                normalized_id='',
                platform=cls.platform,
                is_valid=False,
                error=str(e)
            )
    
    @classmethod
    def scrape(cls, context: ScraperContext) -> BusinessProfile:
        """
        Fetch Instagram profile data via HikerAPI.
        """
        import requests
        
        profile = BusinessProfile()
        profile.slug = context.normalized_id
        
        try:
            print(f"[InstagramScraper] Fetching @{context.normalized_id}...")
            
            response = requests.get(
                f"{cls.API_BASE}/a2/user",
                params={"username": context.normalized_id},
                headers=context.headers,
                timeout=20
            )
            response.raise_for_status()
            
            data = response.json()
            user = data.get('graphql', {}).get('user', {})
            
            if not user:
                print("[InstagramScraper] No user data in response")
                return profile
            
            # Core info
            profile.name = user.get('full_name', '') or user.get('username', '')
            profile.description = user.get('biography', '')
            profile.logo_url = user.get('profile_pic_url_hd', '')
            profile.website_url = user.get('external_url', '')
            
            # Stats (followers, following, posts)
            profile.stats = {
                'followers': user.get('edge_followed_by', {}).get('count', 0),
                'following': user.get('edge_follow', {}).get('count', 0),
                'posts': user.get('edge_owner_to_timeline_media', {}).get('count', 0)
            }
            
            # Recent posts as gallery
            posts = user.get('edge_owner_to_timeline_media', {}).get('edges', [])
            for post in posts[:12]:
                node = post.get('node', {})
                image_url = node.get('display_url')
                if image_url:
                    if not profile.hero_image_url:
                        profile.hero_image_url = image_url
                    else:
                        profile.gallery_images.append(image_url)

            
            # Social link
            profile.social_links.append(SocialLink(
                platform='instagram',
                url=context.metadata.get('profile_url', f"https://instagram.com/{context.normalized_id}")
            ))
            
            print(f"[InstagramScraper] ✓ Found: {profile.name}")
            
        except Exception as e:
            print(f"[InstagramScraper] Error: {e}")
        
        return profile
