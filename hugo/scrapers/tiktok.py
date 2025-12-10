"""
TikTok Scraper

Extends BaseScraper to provide TikTok profile extraction via hydration JSON.
"""
import json
import re
import requests
from typing import ClassVar, Set

from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.schemas import BusinessProfile, SocialLink


class TikTokScraper(BaseScraper):
    """
    Scraper for TikTok profiles.
    
    Supported fields:
        name (username), description (bio), logo_url (avatar),
        gallery_images (video covers), website_url (bio link)
    """
    
    platform: ClassVar[str] = "tiktok"
    
    supported_fields: ClassVar[Set[str]] = {
        'name', 'description', 'logo_url', 'gallery_images', 'website_url', 'stats'
    }
    
    @classmethod
    def can_handle(cls, identifier: str) -> bool:
        """Check if this looks like a TikTok URL or username."""
        if not identifier:
            return False
        lower = identifier.lower()
        return 'tiktok.com' in lower or identifier.startswith('@tiktok:')
    
    @classmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Extract username and prepare request headers.
        """
        try:
            # Extract username
            if 'tiktok.com/@' in identifier:
                username = identifier.split('@')[-1].split('?')[0].split('/')[0]
            elif identifier.startswith('@tiktok:'):
                username = identifier[8:]
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
                    error="Invalid TikTok username"
                )
            
            return ScraperContext(
                identifier=identifier,
                normalized_id=username,
                platform=cls.platform,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': 'https://www.tiktok.com/',
                },
                metadata={
                    'url': f"https://www.tiktok.com/@{username}?lang=en"
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
        Fetch TikTok profile via hydration JSON parsing.
        """
        profile = BusinessProfile()
        profile.slug = context.normalized_id
        profile.name = context.normalized_id
        
        url = context.metadata.get('url')
        
        try:
            print(f"[TikTokScraper] Fetching {url}...")
            
            response = requests.get(url, headers=context.headers, timeout=15)
            content = response.text
            
            # Try __UNIVERSAL_DATA_FOR_REHYDRATION__ first
            script_match = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                content, re.DOTALL
            )
            
            if script_match:
                try:
                    universal_data = json.loads(script_match.group(1))
                    default_scope = universal_data.get('__DEFAULT_SCOPE__', {})
                    user_detail = default_scope.get('webapp.user-detail', {})
                    user_info = user_detail.get('userInfo', {})
                    user = user_info.get('user', {})
                    stats_data = user_info.get('stats', {})
                    
                    profile.name = user.get('uniqueId') or context.normalized_id
                    profile.logo_url = user.get('avatarLarger') or user.get('avatarMedium', '')
                    profile.description = user.get('signature', '')
                    profile.website_url = user.get('bioLink', {}).get('link', '')
                    
                    # Stats (followers, likes, etc.)
                    profile.stats = {
                        'followers': stats_data.get('followerCount', 0),
                        'following': stats_data.get('followingCount', 0),
                        'likes': stats_data.get('heartCount', 0),
                        'videos': stats_data.get('videoCount', 0)
                    }
                    
                except json.JSONDecodeError:
                    pass

            
            # Fallback: SIGI_STATE
            sigi_match = re.search(
                r'<script id="SIGI_STATE" type="application/json">(.*?)</script>',
                content
            )
            
            if sigi_match and not profile.logo_url:
                try:
                    sigi_data = json.loads(sigi_match.group(1))
                    user_module = sigi_data.get('UserModule', {})
                    users = user_module.get('users', {})
                    
                    if users:
                        username_key = next(iter(users))
                        user = users[username_key]
                        
                        profile.name = user.get('uniqueId') or profile.name
                        profile.logo_url = user.get('avatarLarger', '')
                        profile.description = user.get('signature', '')
                    
                    # Extract video covers as gallery
                    item_module = sigi_data.get('ItemModule', {})
                    for item_id, item in list(item_module.items())[:12]:
                        cover = item.get('video', {}).get('cover')
                        if cover:
                            if not profile.hero_image_url:
                                profile.hero_image_url = cover
                            else:
                                profile.gallery_images.append(cover)
                                
                except json.JSONDecodeError:
                    pass
            
            # Social link
            profile.social_links.append(SocialLink(
                platform='tiktok',
                url=f"https://tiktok.com/@{context.normalized_id}"
            ))
            
            print(f"[TikTokScraper] ✓ Found: {profile.name}")
            
        except Exception as e:
            print(f"[TikTokScraper] Error: {e}")
        
        return profile
