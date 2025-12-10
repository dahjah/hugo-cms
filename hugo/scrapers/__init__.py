"""
Hugo Scrapers Package

All scrapers extend BaseScraper with consistent connect/scrape interface.
"""
from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.scrapers.yelp import YelpScraper
from hugo.scrapers.instagram import InstagramScraper
from hugo.scrapers.ftl import FoodTruckLeagueScraper
from hugo.scrapers.tiktok import TikTokScraper
from hugo.scrapers.twitter import TwitterScraper
from hugo.scrapers.psychologytoday import PsychologyTodayScraper

# Registry of all available scrapers
SCRAPERS = [
    YelpScraper,
    InstagramScraper,
    FoodTruckLeagueScraper,
    TikTokScraper,
    TwitterScraper,
    PsychologyTodayScraper,
]

def get_scraper_for_url(identifier: str) -> type:
    """
    Auto-detect which scraper can handle the given URL/identifier.
    Returns the scraper class or None.
    """
    for scraper_cls in SCRAPERS:
        if scraper_cls.can_handle(identifier):
            return scraper_cls
    return None

__all__ = [
    'BaseScraper',
    'ScraperContext',
    'YelpScraper',
    'InstagramScraper',
    'FoodTruckLeagueScraper',
    'TikTokScraper',
    'TwitterScraper',
    'PsychologyTodayScraper',
    'SCRAPERS',
    'get_scraper_for_url',
]


