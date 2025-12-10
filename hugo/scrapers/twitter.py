"""
Twitter/X Scraper

Extends BaseScraper to provide Twitter profile extraction via OG tags.
"""
import re
import html
import requests
from typing import ClassVar, Set

from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.schemas import BusinessProfile, SocialLink


class TwitterScraper(BaseScraper):
    """
    Scraper for Twitter/X profiles.
    
    Uses Slackbot User-Agent to get server-rendered OG tags.
    
    Supported fields:
        name, description (bio), logo_url (profile pic)
    """
    
    platform: ClassVar[str] = "twitter"
    
    supported_fields: ClassVar[Set[str]] = {
        'name', 'description', 'logo_url'
    }
    
    @classmethod
    def can_handle(cls, identifier: str) -> bool:
        """Check if this looks like a Twitter/X URL or handle."""
        if not identifier:
            return False
        lower = identifier.lower()
        return 'twitter.com' in lower or 'x.com' in lower or identifier.startswith('@twitter:')
    
    @classmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Extract username and prepare request headers.
        """
        try:
            # Extract username
            if 'twitter.com/' in identifier or 'x.com/' in identifier:
                # Handle both twitter.com/user and x.com/user
                parts = identifier.split('/')
                username = parts[-1].split('?')[0]
            elif identifier.startswith('@twitter:'):
                username = identifier[9:]
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
                    error="Invalid Twitter username"
                )
            
            return ScraperContext(
                identifier=identifier,
                normalized_id=username,
                platform=cls.platform,
                headers={
                    # Slackbot UA often gets better OG tag rendering
                    'User-Agent': 'Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                metadata={
                    'url': f"https://x.com/{username}"
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
        Fetch Twitter profile via OG meta tags.
        """
        profile = BusinessProfile()
        profile.slug = context.normalized_id
        profile.name = context.normalized_id
        
        url = context.metadata.get('url')
        
        try:
            print(f"[TwitterScraper] Fetching {url}...")
            
            response = requests.get(url, headers=context.headers, timeout=15)
            content = response.text
            
            def get_meta(prop_name):
                """Extract meta tag content."""
                # Standard format
                match = re.search(
                    r'<meta\s+(?:property|name)=["\']' + re.escape(prop_name) + 
                    r'["\']\s+content=["\']([^"\']+)["\']',
                    content
                )
                if match:
                    return html.unescape(match.group(1))
                # Reversed attributes
                match_rev = re.search(
                    r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']' + 
                    re.escape(prop_name) + r'["\']',
                    content
                )
                if match_rev:
                    return html.unescape(match_rev.group(1))
                return ''
            
            # Parse OG tags
            og_title = get_meta('og:title')
            if og_title:
                # Format: "Name (@screen_name) on X"
                name_match = re.match(r'(.*?) \(@(.*?)\) on X', og_title)
                if name_match:
                    profile.name = name_match.group(1)
                else:
                    profile.name = og_title
            
            profile.description = get_meta('og:description')
            profile.logo_url = get_meta('og:image')
            
            # Set hero image from profile pic
            if profile.logo_url:
                profile.hero_image_url = profile.logo_url
            
            # Social link
            profile.social_links.append(SocialLink(
                platform='twitter',
                url=f"https://x.com/{context.normalized_id}"
            ))
            
            print(f"[TwitterScraper] ✓ Found: {profile.name}")
            
        except Exception as e:
            print(f"[TwitterScraper] Error: {e}")
        
        return profile
