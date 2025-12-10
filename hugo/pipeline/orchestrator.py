"""
Scraper Orchestrator

Detects URL types and runs appropriate scrapers, merging results into a BusinessProfile.
Uses the unified BaseScraper interface with connect/scrape pattern.
"""
import re
from typing import List, Dict, Type
from hugo.schemas import BusinessProfile
from hugo.scrapers import get_scraper_for_url, SCRAPERS, BaseScraper, ScraperContext


def orchestrate(inputs: List[str]) -> BusinessProfile:
    """
    Main orchestration function.
    
    Takes a list of URLs/identifiers, auto-detects scrapers, runs connect/scrape,
    and merges all results into one BusinessProfile.
    
    Prioritization: Yelp > FTL > Instagram (for name/core data)
    
    Args:
        inputs: List of URLs or identifiers (e.g., Yelp URL, @instagram, FTL URL)
    
    Returns:
        Merged BusinessProfile
    """
    # Collect results by platform
    results: Dict[str, BusinessProfile] = {}
    
    for input_str in inputs:
        # Auto-detect scraper
        scraper_cls = get_scraper_for_url(input_str)
        
        if not scraper_cls:
            print(f"[Orchestrator] No scraper found for: {input_str}")
            continue
        
        platform = scraper_cls.platform
        print(f"[Orchestrator] Detected {platform}: {input_str}")
        
        try:
            # Step 1: Connect
            context = scraper_cls.connect(input_str)
            
            if not context.is_valid:
                print(f"[Orchestrator] Connection failed for {platform}: {context.error}")
                continue
            
            # Step 2: Scrape
            profile = scraper_cls.scrape(context)
            
            if profile and profile.name:
                results[platform] = profile
                print(f"[Orchestrator] ✓ Scraped {platform}: {profile.name}")
            else:
                print(f"[Orchestrator] No data returned from {platform}")
                
        except Exception as e:
            print(f"[Orchestrator] Error scraping {platform}: {e}")
    
    # Merge in priority order
    final = BusinessProfile()
    priority_order = ['yelp', 'ftl', 'instagram', 'twitter', 'tiktok', 'facebook']
    
    for platform in priority_order:
        if platform in results:
            final.merge(results[platform])
    
    # Ensure minimum viable data
    if not final.name:
        raise ValueError("Could not extract a name from any source")
    
    if not final.hero_image_url and not final.logo_url:
        print("[Orchestrator] Warning: No profile image found")
    
    # Generate slug from name if not set
    if not final.slug:
        final.slug = re.sub(r'[^a-z0-9]+', '-', final.name.lower()).strip('-')
    
    return final


def orchestrate_with_scrapers(
    scraper_inputs: List[tuple[Type[BaseScraper], str]]
) -> BusinessProfile:
    """
    Explicit orchestration where caller specifies which scraper to use for each input.
    
    Args:
        scraper_inputs: List of (ScraperClass, identifier) tuples
    
    Returns:
        Merged BusinessProfile
    
    Example:
        from hugo.scrapers import YelpScraper, InstagramScraper
        
        profile = orchestrate_with_scrapers([
            (YelpScraper, "the-salty-pineapple"),
            (InstagramScraper, "@thesaltypineapple")
        ])
    """
    results: Dict[str, BusinessProfile] = {}
    
    for scraper_cls, identifier in scraper_inputs:
        platform = scraper_cls.platform
        
        try:
            context = scraper_cls.connect(identifier)
            if context.is_valid:
                profile = scraper_cls.scrape(context)
                if profile:
                    results[platform] = profile
        except Exception as e:
            print(f"[Orchestrator] Error: {e}")
    
    # Merge
    final = BusinessProfile()
    for profile in results.values():
        final.merge(profile)
    
    if not final.slug and final.name:
        final.slug = re.sub(r'[^a-z0-9]+', '-', final.name.lower()).strip('-')
    
    return final

