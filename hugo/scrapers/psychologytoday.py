"""
Psychology Today Scraper

Extends BaseScraper to provide therapist profile extraction from Psychology Today.
"""
import re
import json
import html
import requests
from typing import ClassVar, Set
from bs4 import BeautifulSoup

from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.schemas import BusinessProfile, SocialLink


class PsychologyTodayScraper(BaseScraper):
    """
    Scraper for Psychology Today therapist profiles.
    
    Supported fields:
        name, description (bio), logo_url (photo), location_str,
        phone, categories (specialties), hours
    """
    
    platform: ClassVar[str] = "psychologytoday"
    
    supported_fields: ClassVar[Set[str]] = {
        'name', 'description', 'logo_url', 'hero_image_url',
        'location_str', 'phone', 'categories'
    }
    
    @classmethod
    def can_handle(cls, identifier: str) -> bool:
        """Check if this looks like a Psychology Today URL."""
        if not identifier:
            return False
        return 'psychologytoday.com' in identifier.lower()
    
    @classmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Validate Psychology Today URL.
        """
        try:
            if 'psychologytoday.com' not in identifier:
                return ScraperContext(
                    identifier=identifier,
                    normalized_id='',
                    platform=cls.platform,
                    is_valid=False,
                    error="Not a Psychology Today URL"
                )
            
            # Extract profile ID if possible
            # URLs like: psychologytoday.com/us/therapists/therapist-name/123456
            profile_id = ''
            parts = identifier.rstrip('/').split('/')
            if parts:
                profile_id = parts[-1]
            
            return ScraperContext(
                identifier=identifier,
                normalized_id=profile_id or identifier,
                platform=cls.platform,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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
        Fetch Psychology Today profile via BeautifulSoup.
        """
        profile = BusinessProfile()
        url = context.metadata.get('url', context.identifier)
        
        try:
            print(f"[PsychologyTodayScraper] Fetching {url}...")
            
            response = requests.get(url, headers=context.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Name - usually in h1 or specific class
            name_el = soup.find('h1', class_='profile-title') or soup.find('h1')
            if name_el:
                profile.name = name_el.get_text(strip=True)
            
            # Generate slug from name
            if profile.name:
                profile.slug = re.sub(r'[^a-z0-9]+', '-', profile.name.lower()).strip('-')
            
            # Profile photo
            photo_el = soup.find('img', class_='profile-photo') or soup.find('img', {'alt': lambda x: x and 'photo' in x.lower()})
            if photo_el and photo_el.get('src'):
                profile.logo_url = photo_el['src']
                profile.hero_image_url = photo_el['src']
            
            # Bio/Statement
            bio_el = soup.find('div', class_='profile-statement') or soup.find('div', class_='bio')
            if bio_el:
                profile.description = bio_el.get_text(strip=True)
            else:
                # Try meta description
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    profile.description = meta_desc.get('content', '')
            
            # Location
            location_el = soup.find('div', class_='profile-location') or soup.find('address')
            if location_el:
                profile.location_str = location_el.get_text(strip=True)
                profile.address = profile.location_str
            
            # Phone
            phone_el = soup.find('a', href=lambda x: x and x.startswith('tel:'))
            if phone_el:
                profile.phone = phone_el.get_text(strip=True) or phone_el['href'].replace('tel:', '')
            
            # Specialties as categories
            specialties_section = soup.find('div', class_='specialties') or soup.find('ul', class_='spec-list')
            if specialties_section:
                items = specialties_section.find_all('li') or specialties_section.find_all('span')
                profile.categories = [item.get_text(strip=True) for item in items[:10]]
            
            # Try JSON-LD structured data
            script_ld = soup.find('script', type='application/ld+json')
            if script_ld:
                try:
                    ld_data = json.loads(script_ld.string)
                    if isinstance(ld_data, list):
                        ld_data = ld_data[0] if ld_data else {}
                    
                    if not profile.name:
                        profile.name = ld_data.get('name', '')
                    if not profile.logo_url:
                        profile.logo_url = ld_data.get('image', '')
                    if not profile.phone:
                        profile.phone = ld_data.get('telephone', '')
                    if not profile.address:
                        addr = ld_data.get('address', {})
                        if isinstance(addr, dict):
                            profile.address = f"{addr.get('streetAddress', '')}, {addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}"
                            profile.location_str = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}"
                except json.JSONDecodeError:
                    pass
            
            # Social link
            profile.social_links.append(SocialLink(
                platform='psychologytoday',
                url=url
            ))
            
            # Add therapy-related categories if none found
            if not profile.categories:
                profile.categories = ['Therapist', 'Mental Health']
            
            print(f"[PsychologyTodayScraper] ✓ Found: {profile.name}")
            
        except Exception as e:
            print(f"[PsychologyTodayScraper] Error: {e}")
        
        return profile
