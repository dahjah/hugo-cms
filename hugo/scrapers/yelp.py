"""
Yelp Scraper

Extends BaseScraper to provide Yelp business profile extraction.
"""
import json
import re
import html
import time
import asyncio
import requests
from typing import ClassVar, Set

from hugo.scrapers.base import BaseScraper, ScraperContext
from hugo.schemas import BusinessProfile, MenuItem, Review, SocialLink

# Crawlee for anti-fingerprinting fallback
try:
    from crawlee.crawlers import PlaywrightCrawler
    from crawlee.crawlers._playwright import PlaywrightCrawlingContext
    CRAWLEE_AVAILABLE = True
except ImportError:
    CRAWLEE_AVAILABLE = False


class YelpScraper(BaseScraper):
    """
    Scraper for Yelp business pages.
    
    Supported fields:
        name, rating, reviews, menu_items, hours, photos, location, phone, price, categories
    """
    
    platform: ClassVar[str] = "yelp"
    
    supported_fields: ClassVar[Set[str]] = {
        'name', 'rating', 'review_count', 'reviews', 'menu_items',
        'hours', 'photos', 'location_str', 'address', 'phone', 'price_level', 'categories', 'email'
    }
    
    @classmethod
    def can_handle(cls, identifier: str) -> bool:
        """Check if this looks like a Yelp URL or slug."""
        if not identifier:
            return False
        lower = identifier.lower()
        return 'yelp.com' in lower or lower.startswith('@yelp:')
    
    @classmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Validate and normalize Yelp identifier.
        For Yelp, we just extract the slug - actual auth happens during scrape.
        """
        try:
            # Extract slug from various input formats
            if 'yelp.com/biz/' in identifier:
                slug = identifier.split('/biz/')[-1].split('?')[0]
            elif identifier.startswith('@yelp:'):
                slug = identifier[6:]
            else:
                slug = identifier
            
            # Basic validation
            if not slug or len(slug) < 3:
                return ScraperContext(
                    identifier=identifier,
                    normalized_id='',
                    platform=cls.platform,
                    is_valid=False,
                    error="Invalid Yelp slug"
                )
            
            return ScraperContext(
                identifier=identifier,
                normalized_id=slug,
                platform=cls.platform,
                metadata={
                    'url': f"https://www.yelp.com/biz/{slug}",
                    'menu_url': f"https://www.yelp.com/menu/{slug}"
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
        Execute Yelp scrape using Playwright with stealth.
        Falls back to Crawlee with anti-fingerprinting if DataDome blocks.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[YelpScraper] Playwright not installed. Skipping Yelp scraping.")
            return profile

        
        profile = BusinessProfile()
        profile.slug = context.normalized_id

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[YelpScraper] Playwright not installed. Skipping Yelp scraping.")
            return profile

        
        url = context.metadata.get('url', f"https://www.yelp.com/biz/{context.normalized_id}")
        menu_url = context.metadata.get('menu_url', f"https://www.yelp.com/menu/{context.normalized_id}")
        
        enc_biz_id = None
        
        # Use Crawlee to bypass DataDome and get initial page content
        # Use Crawlee to bypass DataDome and get initial page content
        if CRAWLEE_AVAILABLE:
            print(f"[YelpScraper] Fetching {url} with Crawlee (bypassing DataDome)...")
            try:
                crawlee_result = cls._scrape_with_crawlee(url)
                if crawlee_result and crawlee_result.get('content'):
                    content = crawlee_result['content']
                    cookies = crawlee_result.get('cookies') or {}
                    
                    # Parse hydration data from page content
                    enc_biz_id = cls._parse_hydration(content, profile)
                    print(f"[YelpScraper] Extracted from hydration: {profile.name}")
                    
                    # Fetch additional data via batched GQL request (needs datadome cookie for hours)
                    if enc_biz_id:
                        cls._fetch_all_gql_data(enc_biz_id, url, cookies, profile)
                        
                    # Fetch menu with a standalone Playwright session
                    cls._fetch_menu_standalone(menu_url, profile)
            except Exception as e:
                print(f"[YelpScraper] Crawlee Error: {e}")
        else:
             # Fallback: Direct Playwright (Standard)
             print(f"[YelpScraper] Fetching {url} with Playwright (Direct)...")
             try:
                 with sync_playwright() as p:
                     browser = p.chromium.launch(headless=True)
                     page = browser.new_page()
                     
                     # Stealth-ish headers
                     page.set_extra_http_headers({
                         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                         "Accept-Language": "en-US,en;q=0.9"
                     })
                     
                     page.goto(url, timeout=15000)
                     time.sleep(2) # Wait for hydration
                     content = page.content()
                     
                     # Extract cookies
                     cookies = {c['name']: c['value'] for c in page.context.cookies()}
                     
                     enc_biz_id = cls._parse_hydration(content, profile)
                     if enc_biz_id:
                         print(f"[YelpScraper] Hydration successful. EncBizId: {enc_biz_id}")
                         cls._fetch_all_gql_data(enc_biz_id, url, cookies, profile)
                     else:
                         print("[YelpScraper] Failed to extract EncBizId from hydration.")
                         
                     browser.close()
                     
                 # Fetch menu (reuse standalone)
                 cls._fetch_menu_standalone(menu_url, profile)
                 
             except Exception as e:
                 print(f"[YelpScraper] Playwright Direct Error: {e}")

        
        # Add social link
        profile.social_links.append(SocialLink(
            platform='yelp',
            url=url
        ))
        
        return profile
    
    @classmethod
    def _parse_hydration(cls, content: str, profile: BusinessProfile) -> str:
        """Parse hydration JSON from page content."""
        scripts = re.findall(r'<script[^>]*type=\"application/json\"[^>]*>(.*?)</script>', content, re.DOTALL)
        enc_biz_id = None
        
        for script_content in scripts:
            try:
                clean = script_content.replace('<!--', '').replace('-->', '')
                payload = json.loads(html.unescape(clean))
                
                if not isinstance(payload, dict):
                    continue
                
                # PATTERN 1: Apollo cache format - Business:encid keys
                for key, val in payload.items():
                    if key.startswith('Business:') and isinstance(val, dict):
                        if not profile.name and val.get('name'):
                            profile.name = val.get('name', '')
                            enc_biz_id = val.get('encid') or key.split(':')[1]
                            print(f"[YelpScraper] Hydration found encid: {enc_biz_id}")
                            
                            # Price
                            profile.price_level = val.get('priceRange', '')
                            
                            # Phone (may be a ref or dict)
                            phone_data = val.get('phoneNumber', '')
                            if isinstance(phone_data, dict):
                                profile.phone = phone_data.get('formatted', '') or phone_data.get('value', '')
                            elif isinstance(phone_data, str):
                                profile.phone = phone_data
                            
                            # Rating - key has params like rating({"roundingMethod":"NEAREST_TENTH"})
                            for k, v in val.items():
                                if k.startswith('rating(') and isinstance(v, (int, float)):
                                    profile.stats['rating'] = v
                            
                            # Review count
                            if val.get('reviewCount'):
                                profile.stats['review_count'] = val.get('reviewCount')
                            
                            # Primary photo
                            primary = val.get('primaryPhoto', {})
                            if isinstance(primary, dict):
                                photo_url = primary.get('photoUrl', {})
                                if isinstance(photo_url, dict):
                                    for k, v in photo_url.items():
                                        if 'url(' in k and v:
                                            profile.hero_image_url = v
                                            break
                            
                            # Location
                            loc = val.get('location', {})
                            if isinstance(loc, dict):
                                addr = loc.get('address', {})
                                if isinstance(addr, dict):
                                    city = addr.get('city', '')
                                    state = addr.get('regionCode', '') or addr.get('state', '')
                                    profile.location_str = f"{city}, {state}" if city else ''
                            
                            # Categories - resolve refs from payload
                            cat_refs = val.get('categories', [])
                            if isinstance(cat_refs, list):
                                for ref in cat_refs:
                                    if isinstance(ref, dict) and '__ref' in ref:
                                        cat_key = ref['__ref']
                                        cat_data = payload.get(cat_key, {})
                                        if isinstance(cat_data, dict) and cat_data.get('title'):
                                            profile.categories.append(cat_data['title'])
                            
                            # Media/gallery photos - resolve refs
                            media = val.get('media', {})
                            if isinstance(media, dict):
                                for mk, mv in media.items():
                                    if 'orderedMediaItems' in mk and isinstance(mv, dict):
                                        edges = mv.get('edges', [])
                                        for edge in edges:
                                            node = edge.get('node', {})
                                            if '__ref' in node:
                                                photo_key = node['__ref']
                                                photo_data = payload.get(photo_key, {})
                                                if isinstance(photo_data, dict):
                                                    photo_url = photo_data.get('photoUrl', {})
                                                    if isinstance(photo_url, dict):
                                                        for pk, pv in photo_url.items():
                                                            if 'url(' in pk and pv:
                                                                if not profile.hero_image_url:
                                                                    profile.hero_image_url = pv
                                                                else:
                                                                    profile.gallery_images.append(pv)
                                                                break
                            break  # Found business data, exit loop
                
                # PATTERN 2: Legacy format - __typename: Business
                for key, val in payload.items():
                    if isinstance(val, dict) and val.get('__typename') == 'Business':
                        if not profile.name:
                            profile.name = val.get('name', '')
                            phone_data = val.get('phoneNumber', '')
                            if isinstance(phone_data, dict):
                                profile.phone = phone_data.get('formatted', '')
                            else:
                                profile.phone = phone_data or ''
                            profile.price_level = val.get('priceRange', '')
                            enc_biz_id = val.get('encid')
                            print(f"[YelpScraper] Hydration (legacy) found encid: {enc_biz_id}")
            except:
                continue
        
        return enc_biz_id
        return enc_biz_id
    
    @classmethod
    def _fetch_gql_details(cls, page, enc_biz_id: str, profile: BusinessProfile):
        """Fetch details via GraphQL in browser context."""
        gql_payload = {
            "operationName": "GetLocalBusinessJsonLinkedData",
            "variables": {
                "encBizId": enc_biz_id,
                "FetchVideoMetadata": True,
                "MediaItemsLimit": 25,
                "ReviewsPerPage": 10,
                "HasSelectedReview": False,
                "SelectedReviewEncId": ""
            },
            "extensions": {
                "operationType": "query",
                "documentId": "fef220503306ae8dc88ec06e8ec118e326e8856b4cbe13fedcfe4108ef4b5418"
            }
        }
        
        try:
            result = page.evaluate("""async (payload) => {
                const res = await fetch("https://www.yelp.com/gql/batch", {
                    method: "POST",
                    headers: {
                        "content-type": "application/json",
                        "x-apollo-operation-name": "GetLocalBusinessJsonLinkedData"
                    },
                    body: JSON.stringify([payload])
                });
                return await res.json();
            }""", gql_payload)
            
            if isinstance(result, list) and len(result) > 0:
                biz = result[0].get('data', {}).get('business', {})
                
                # Hours
                hours_data = biz.get('operationHours', {}).get('regularHoursMergedWithSpecialHoursForCurrentWeek', [])
                for h in hours_data:
                    day = h.get('dayOfWeekShort')
                    times = h.get('regularHours', [])
                    if day and times:
                        profile.hours.append(f"{day}: {', '.join(times)}")
                
                # Photos
                media = biz.get('media', {}).get('orderedMediaItems', {}).get('edges', [])
                for edge in media:
                    enc_id = edge.get('node', {}).get('encid')
                    if enc_id:
                        url = f"https://s3-media0.fl.yelpcdn.com/bphoto/{enc_id}/l.jpg"
                        if not profile.hero_image_url:
                            profile.hero_image_url = url
                        else:
                            profile.gallery_images.append(url)
                
                # Reviews
                reviews = biz.get('reviews', {}).get('edges', [])
                for edge in reviews:
                    node = edge.get('node', {})
                    text = node.get('text', {})
                    if isinstance(text, dict):
                        text = text.get('full', '')
                    
                    profile.reviews.append(Review(
                        author=node.get('author', {}).get('displayName', ''),
                        rating=node.get('rating', 0),
                        text=text,
                        date=node.get('localizedDate', ''),
                        platform='yelp'
                    ))
                    
        except Exception as e:
            print(f"[YelpScraper] GQL Error: {e}")
    
    @classmethod
    def _fetch_menu(cls, page, menu_url: str, profile: BusinessProfile):
        """Fetch menu items from menu page."""
        try:
            print(f"[YelpScraper] Fetching menu from {menu_url}...")
            page.goto(menu_url, timeout=10000)
            time.sleep(1)
            
            items = page.evaluate("""() => {
                const items = [];
                document.querySelectorAll('.menu-item').forEach(div => {
                    const item = {name: '', description: '', price: ''};
                    const title = div.querySelector('h4');
                    if (title) item.name = title.innerText.trim();
                    const desc = div.querySelector('.menu-item-details-description');
                    if (desc) item.description = desc.innerText.trim();
                    const parent = div.parentElement;
                    if (parent) {
                        const price = parent.querySelector('.menu-item-price-amount');
                        if (price) item.price = price.innerText.trim();
                    }
                    if (item.name) items.push(item);
                });
                return items;
            }""")
            
            for item in items:
                profile.menu_items.append(MenuItem(
                    name=item.get('name', ''),
                    description=item.get('description', ''),
                    price=item.get('price', '')
                ))
                
        except Exception as e:
            print(f"[YelpScraper] Menu Error: {e}")
    
    @classmethod
    def _fetch_menu_standalone(cls, menu_url: str, profile: BusinessProfile):
        """Fetch menu items in a standalone Playwright session (for Crawlee fallback path)."""
        from playwright.sync_api import sync_playwright
        try:
            print(f"[YelpScraper] Fetching menu (standalone) from {menu_url}...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(menu_url, timeout=10000)
                time.sleep(1)
                
                items = page.evaluate("""() => {
                    const items = [];
                    document.querySelectorAll('.menu-item').forEach(div => {
                        const item = {name: '', description: '', price: ''};
                        const title = div.querySelector('h4');
                        if (title) item.name = title.innerText.trim();
                        const desc = div.querySelector('.menu-item-details-description');
                        if (desc) item.description = desc.innerText.trim();
                        const parent = div.parentElement;
                        if (parent) {
                            const price = parent.querySelector('.menu-item-price-amount');
                            if (price) item.price = price.innerText.trim();
                        }
                        if (item.name) items.push(item);
                    });
                    return items;
                }""")
                
                for item in items:
                    profile.menu_items.append(MenuItem(
                        name=item.get('name', ''),
                        description=item.get('description', ''),
                        price=item.get('price', '')
                    ))
                
                browser.close()
                
        except Exception as e:
            print(f"[YelpScraper] Menu Standalone Error: {e}")
    
    @classmethod
    async def _crawlee_fetch(cls, url: str) -> dict:
        """
        Internal async function to fetch content using Crawlee.
        Returns dict with 'content' and 'cookies'.
        """
        result = {'content': '', 'cookies': {}}
        
        crawler = PlaywrightCrawler(
            # Fingerprint generator for anti-detection (Crawlee 1.2.0 API)
            fingerprint_generator='default',
            headless=True,
        )

        @crawler.router.default_handler
        async def request_handler(context: PlaywrightCrawlingContext):
            page = context.page
            # Wait for hydration
            try:
                await page.wait_for_selector('h1', timeout=10000)
                await page.wait_for_timeout(2000)
            except:
                pass
                
            result['content'] = await page.content()
            
            # Extract cookies for later GraphQL requests (Crawlee 1.2.0 API)
            try:
                browser_context = page.context
                cookies = await browser_context.cookies()
                result['cookies'] = {c['name']: c['value'] for c in cookies}
            except Exception as e:
                print(f"[YelpScraper] Cookie extraction failed: {e}")

        await crawler.run([url])
        return result
    
    @classmethod
    def _scrape_with_crawlee(cls, url: str) -> dict:
        """
        Synchronous wrapper for Crawlee fetch.
        Uses a new event loop to avoid conflicts with Playwright's sync_playwright.
        """
        if not CRAWLEE_AVAILABLE:
            print("[YelpScraper] Crawlee not installed, skipping fallback.")
            return None
            
        try:
            print(f"[YelpScraper] Fallback: Fetching {url} with Crawlee...")
            # Create a new event loop to avoid nesting issues with Playwright
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(cls._crawlee_fetch(url))
            finally:
                loop.close()
        except Exception as e:
            print(f"[YelpScraper] Crawlee Error: {e}")
            return None
    
    @classmethod
    def _fetch_all_gql_data(cls, enc_biz_id: str, referer_url: str, cookies: dict, profile: BusinessProfile):
        """
        Fetch all GQL data in a single batched request (hours, reviews, extra details).
        """
        url = "https://www.yelp.com/gql/batch"
        
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "referer": referer_url,
            "x-apollo-operation-name": "GetLocalBusinessJsonLinkedData,GetBusinessReviewFeed,GetExtraHeadTagsBizDetails"
        }

        # Batch all 3 operations into one request
        payload = [
            # Operation 1: Hours & Photos
            {
                "operationName": "GetLocalBusinessJsonLinkedData",
                "variables": {
                    "encBizId": enc_biz_id,
                    "FetchVideoMetadata": True,
                    "MediaItemsLimit": 25,
                    "FetchVideoCarouselItems": False,
                    "VideoCarouselItemsLimit": 7,
                    "ReviewsPerPage": 10,
                    "HasSelectedReview": False,
                    "SelectedReviewEncId": ""
                },
                "extensions": {
                    "operationType": "query",
                    "documentId": "fef220503306ae8dc88ec06e8ec118e326e8856b4cbe13fedcfe4108ef4b5418"
                }
            },
            # Operation 2: Reviews
            {
                "operationName": "GetBusinessReviewFeed",
                "variables": {
                    "eliteAllStarSourceFlow": "biz_page_review_feed",
                    "encBizId": enc_biz_id,
                    "reviewsPerPage": 10,
                    "selectedReviewEncId": "",
                    "hasSelectedReview": False,
                    "sortBy": "RELEVANCE_DESC",
                    "ratings": [5, 4, 3, 2, 1],
                    "queryText": "",
                    "isSearching": False,
                    "after": None,
                    "isTranslating": False,
                    "translateLanguageCode": "en",
                    "reactionsSourceFlow": "businessPageReviewSection",
                    "minConfidenceLevel": "HIGH_CONFIDENCE",
                    "highlightType": "",
                    "highlightIdentifier": "",
                    "isHighlighting": False,
                    "shouldFetchAddress": True
                },
                "extensions": {
                    "operationType": "query",
                    "documentId": "66db1c3377fb0a5ecc4d765d33263be3bd14f178868e0824687e4836c5104ee1"
                }
            },
            # Operation 3: Extra Details (specialties, etc.)
            {
                "operationName": "GetExtraHeadTagsBizDetails",
                "variables": {
                    "BizEncId": enc_biz_id,
                    "RequestUrl": referer_url,
                    "ReviewEncId": "",
                    "ReviewIsSelected": False
                },
                "extensions": {
                    "operationType": "query",
                    "documentId": "d71d5fd44e5a5d0b3610cbe12c3b7d84e007acbd437914f5c03055674aa0331b"
                }
            }
        ]

        try:
            response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 3:
                    # Response 0: Hours & Photos
                    biz_details = data[0].get('data', {}).get('business', {})
                    
                    # Hours
                    hours_data = biz_details.get('operationHours') or {}
                    if isinstance(hours_data, dict):
                        regular_hours = hours_data.get('regularHoursMergedWithSpecialHoursForCurrentWeek', [])
                        for h in regular_hours:
                            day = h.get('dayOfWeekShort')
                            times = h.get('regularHours', [])
                            if day and times:
                                profile.hours.append(f"{day}: {', '.join(times)}")
                    
                    # Photos (from GQL, though we already have from hydration)
                    media = biz_details.get('media', {}).get('orderedMediaItems', {}).get('edges', [])
                    for edge in media:
                        enc_id = edge.get('node', {}).get('encid')
                        if enc_id:
                            img_url = f"https://s3-media0.fl.yelpcdn.com/bphoto/{enc_id}/l.jpg"
                            if not profile.hero_image_url:
                                profile.hero_image_url = img_url
                            elif img_url not in profile.gallery_images:
                                profile.gallery_images.append(img_url)
                    
                    # Response 1: Reviews
                    biz_reviews = data[1].get('data', {}).get('business', {})
                    reviews_data = biz_reviews.get('reviews', {}).get('edges', [])
                    for edge in reviews_data:
                        node = edge.get('node', {})
                        text = node.get('text', {})
                        if isinstance(text, dict):
                            text = text.get('full', '')
                        
                        author = node.get('author', {})
                        photo = author.get('profilePhoto') or {}
                        photo_url = photo.get('src') or photo.get('url') or ""
                        
                        profile.reviews.append(Review(
                            author=author.get('displayName', ''),
                            rating=node.get('rating', 0),
                            text=text,
                            date=node.get('localizedDate', ''),
                            author_image=photo_url,
                            platform='yelp'
                        ))
                    
                    # Response 2: Extra Details
                    biz_extra = data[2].get('data', {}).get('business', {})
                    
                    # Specialties - use as description if not already set
                    specialties = biz_extra.get('specialties', '')
                    if specialties and not profile.description:
                        profile.description = specialties
                    
                    # History
                    history = biz_extra.get('history', {})
                    if isinstance(history, dict):
                        hist_desc = history.get('description', '')
                        if hist_desc and not profile.description:
                            profile.description = hist_desc

                    # Email extraction using BaseScraper helper
                    if not profile.email:
                        hist_text = history.get('description') if isinstance(history, dict) else ""
                        combined_text = (specialties or "") + " " + (hist_text or "")
                        email = cls._extract_email(combined_text)
                        if email:
                            profile.email = email
                    
                    print(f"[YelpScraper] Batched GQL: {len(profile.hours)} hours, {len(profile.gallery_images)} photos, {len(profile.reviews)} reviews, description={'Yes' if profile.description else 'No'}")
                        
        except Exception as e:
            print(f"[YelpScraper] Batched GQL Error: {e}")
    
    @classmethod
    def _fetch_gql_details_requests(cls, enc_biz_id: str, referer_url: str, cookies: dict, profile: BusinessProfile):
        """
        Fetch details using requests + harvested cookies (fallback for Crawlee flow).
        """
        url = "https://www.yelp.com/gql/batch"
        
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.yelp.com",
            "referer": referer_url,
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/141.0.0.0 Safari/537.36",
            "x-apollo-operation-name": "GetLocalBusinessJsonLinkedData"
        }

        payload = [{
            "operationName": "GetLocalBusinessJsonLinkedData",
            "variables": {
                "encBizId": enc_biz_id,
                "FetchVideoMetadata": True,
                "MediaItemsLimit": 25,
                "FetchVideoCarouselItems": False,
                "VideoCarouselItemsLimit": 7,
                "ReviewsPerPage": 10,
                "HasSelectedReview": False,
                "SelectedReviewEncId": ""
            },
            "extensions": {
                "operationType": "query",
                "documentId": "fef220503306ae8dc88ec06e8ec118e326e8856b4cbe13fedcfe4108ef4b5418"
            }
        }]

        try:
            response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    biz = data[0].get('data', {}).get('business', {})
                    
                    # Hours
                    hours_data = biz.get('operationHours') or {}
                    if isinstance(hours_data, dict):
                        regular_hours = hours_data.get('regularHoursMergedWithSpecialHoursForCurrentWeek', [])
                        for h in regular_hours:
                            day = h.get('dayOfWeekShort')
                            times = h.get('regularHours', [])
                            if day and times:
                                profile.hours.append(f"{day}: {', '.join(times)}")
                    
                    # Photos
                    media = biz.get('media', {}).get('orderedMediaItems', {}).get('edges', [])
                    for edge in media:
                        enc_id = edge.get('node', {}).get('encid')
                        if enc_id:
                            img_url = f"https://s3-media0.fl.yelpcdn.com/bphoto/{enc_id}/l.jpg"
                            if not profile.hero_image_url:
                                profile.hero_image_url = img_url
                            else:
                                profile.gallery_images.append(img_url)
                    
                    print(f"[YelpScraper] GQL via requests: {len(profile.hours)} hours, {len(profile.gallery_images)} photos")
                        
        except Exception as e:
            print(f"[YelpScraper] GQL Requests Error: {e}")

    @classmethod
    def _fetch_reviews_requests(cls, enc_biz_id: str, referer_url: str, cookies: dict, profile: BusinessProfile):
        """
        Fetch reviews using GetBusinessReviewFeed GQL query.
        """
        url = "https://www.yelp.com/gql/batch"
        
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.yelp.com",
            "referer": referer_url,
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/141.0.0.0 Safari/537.36",
            "x-apollo-operation-name": "GetBusinessReviewFeed"
        }

        payload = [{
            "operationName": "GetBusinessReviewFeed",
            "variables": {
                "eliteAllStarSourceFlow": "biz_page_review_feed",
                "encBizId": enc_biz_id,
                "reviewsPerPage": 10,
                "selectedReviewEncId": "",
                "hasSelectedReview": False,
                "sortBy": "RELEVANCE_DESC",
                "ratings": [5, 4, 3, 2, 1],
                "queryText": "",
                "isSearching": False,
                "after": None,
                "isTranslating": False,
                "translateLanguageCode": "en",
                "reactionsSourceFlow": "businessPageReviewSection",
                "minConfidenceLevel": "HIGH_CONFIDENCE",
                "highlightType": "",
                "highlightIdentifier": "",
                "isHighlighting": False,
                "shouldFetchAddress": True
            },
            "extensions": {
                "operationType": "query",
                "documentId": "66db1c3377fb0a5ecc4d765d33263be3bd14f178868e0824687e4836c5104ee1"
            }
        }]

        try:
            response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    biz = data[0].get('data', {}).get('business', {})
                    reviews_data = biz.get('reviews', {}).get('edges', [])
                    
                    for edge in reviews_data:
                        node = edge.get('node', {})
                        text = node.get('text', {})
                        if isinstance(text, dict):
                            text = text.get('full', '')
                        
                        author = node.get('author', {})
                        profile.reviews.append(Review(
                            author=author.get('displayName', ''),
                            rating=node.get('rating', 0),
                            text=text,
                            date=node.get('localizedDate', ''),
                            platform='yelp'
                        ))
                    
                    print(f"[YelpScraper] Reviews: {len(profile.reviews)} fetched")
                        
        except Exception as e:
            print(f"[YelpScraper] Reviews Fetch Error: {e}")

    @classmethod
    def _fetch_extra_details_requests(cls, enc_biz_id: str, referer_url: str, cookies: dict, profile: BusinessProfile):
        """
        Fetch extra details like specialties using GetExtraHeadTagsBizDetails GQL query.
        """
        url = "https://www.yelp.com/gql/batch"
        
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "referer": referer_url,
            "x-apollo-operation-name": "GetExtraHeadTagsBizDetails"
        }

        payload = [{
            "operationName": "GetExtraHeadTagsBizDetails",
            "variables": {
                "BizEncId": enc_biz_id,
                "RequestUrl": referer_url,
                "ReviewEncId": "",
                "ReviewIsSelected": False
            },
            "extensions": {
                "operationType": "query",
                "documentId": "d71d5fd44e5a5d0b3610cbe12c3b7d84e007acbd437914f5c03055674aa0331b"
            }
        }]

        try:
            response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    biz = data[0].get('data', {}).get('business', {})
                    
                    # Specialties - use as description if not already set
                    specialties = biz.get('specialties', '')
                    if specialties and not profile.description:
                        profile.description = specialties
                    
                    # History
                    history = biz.get('history', {})
                    if isinstance(history, dict):
                        hist_desc = history.get('description', '')
                        if hist_desc and not profile.description:
                            profile.description = hist_desc
                    
                    print(f"[YelpScraper] Extra details: description={'Yes' if profile.description else 'No'}")
                        
        except Exception as e:
            print(f"[YelpScraper] Extra Details Fetch Error: {e}")

