"""
Food Truck League Scraper

Extends BaseScraper to provide FTL profile extraction.
"""
import json
from typing import ClassVar, Set
from urllib.parse import urljoin

from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.schemas import BusinessProfile, SocialLink


class FoodTruckLeagueScraper(BaseScraper):
    """
    Scraper for Food Truck League profiles.
    
    Supported fields:
        name, tagline (subtitle), description (bio), logo_url, booking_url
    """
    
    platform: ClassVar[str] = "ftl"
    
    supported_fields: ClassVar[Set[str]] = {
        'name', 'tagline', 'description', 'logo_url',
        'gallery_images', 'booking_url', 'location_str'
    }
    
    @classmethod
    def can_handle(cls, identifier: str) -> bool:
        """Check if this looks like a FTL URL."""
        if not identifier:
            return False
        return 'foodtruckleague.com' in identifier.lower()
    
    @classmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Validate FTL URL.
        """
        try:
            if 'foodtruckleague.com' not in identifier:
                return ScraperContext(
                    identifier=identifier,
                    normalized_id='',
                    platform=cls.platform,
                    is_valid=False,
                    error="Not a Food Truck League URL"
                )
            
            return ScraperContext(
                identifier=identifier,
                normalized_id=identifier,  # Use full URL as ID
                platform=cls.platform,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36'
                },
                metadata={'url': identifier}
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
        Fetch FTL profile via BeautifulSoup.
        """
        import requests
        from bs4 import BeautifulSoup
        
        profile = BusinessProfile()
        url = context.normalized_id
        
        try:
            print(f"[FTLScraper] Fetching {url}...")
            
            response = requests.get(url, headers=context.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Name
            name_tag = soup.find('h2', class_='font-bold')
            if name_tag:
                profile.name = name_tag.get_text(strip=True)
            
            # Subtitle/Tagline
            subtitle_tag = soup.find('div', class_='my-10')
            if subtitle_tag:
                profile.tagline = subtitle_tag.get_text(strip=True)
            
            # Bio/Story
            story_div = soup.find('div', class_='relative mb-10')
            if story_div:
                p_tag = story_div.find('p')
                if p_tag:
                    profile.description = p_tag.get_text(strip=True)
            
            # Images - collect all CDN images
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                # Skip small icons/placeholders
                if 'placeholder' in src.lower() or len(src) < 20:
                    continue
                    
                absolute_url = urljoin(url, src)
                
                # Identify logo specifically
                if 'truckLogo' in alt or 'logo' in alt.lower():
                    profile.logo_url = absolute_url
                elif 'cdn.files.smartsuite.com' in src or 'cdn' in src.lower():
                    # Food/truck images go to gallery
                    if not profile.hero_image_url:
                        profile.hero_image_url = absolute_url
                    else:
                        profile.gallery_images.append(absolute_url)
            
            # Booking link
            book_button = soup.find('button', string='Book this truck')
            if book_button:
                parent_link = book_button.find_parent('a')
                if parent_link and parent_link.get('href'):
                    profile.booking_url = urljoin(url, parent_link['href'])
            
            # Generate slug from name
            if profile.name:
                import re
                profile.slug = re.sub(r'[^a-z0-9]+', '-', profile.name.lower()).strip('-')
            
            # Social link
            profile.social_links.append(SocialLink(
                platform='foodtruckleague',
                url=url
            ))
            
            print(f"[FTLScraper] ✓ Found: {profile.name}")
            
        except Exception as e:
            print(f"[FTLScraper] Error: {e}")
        
        return profile
