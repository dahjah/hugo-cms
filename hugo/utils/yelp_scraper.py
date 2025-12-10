import json
import re
import html
import json
import re
import html
import time
import asyncio
from playwright.sync_api import sync_playwright
try:
    from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
    CRAWLEE_AVAILABLE = True
except ImportError:
    CRAWLEE_AVAILABLE = False

def scrape_yelp_business(url_or_slug):
    """
    Scrape business info from a public Yelp profile using Playwright.
    This bypasses DataDome bot protection by executing JavaScript.
    """
    if 'yelp.com' not in url_or_slug:
        url = f"https://www.yelp.com/biz/{url_or_slug}"
    else:
        url = url_or_slug
        
    data = {
        'name': '',
        'rating': 0.0,
        'review_count': 0,
        'location': '',
        'photos': [],
        'categories': [],
        'phone': '',
        'price': '',
        'menu_items': [],
        'menu_url': '',
        'reviews': [],
        'hours': []
    }
    
    try:
        with sync_playwright() as p:
            # Emulate a real Chrome browser with stealth flags
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/Denver'
            )
            page = context.new_page()
            
            # Add init script to remove webdriver property
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"Navigating to {url}...")
            page.goto(url, wait_until='domcontentloaded', timeout=10000)
            
            # Wait a bit for hydration/JS challenge
            # page.wait_for_load_state('networkidle') # can be flaky, manual sleep + specific checks better
            time.sleep(2) 
            
            content = page.content()
            
            # 1. Parse Hydration Data (reused logic)
            # Yelp embeds data in <script type="application/json"><!--{...}--></script>
            scripts = re.findall(r'<script[^>]*type=\"application/json\"[^>]*>(.*?)</script>', content, re.DOTALL)
            
            enc_biz_id = None
            
            for script_content in scripts:
                try:
                    clean_content = script_content.replace('<!--', '').replace('-->', '')
                    json_str = html.unescape(clean_content)
                    payload = json.loads(json_str)
                    
                    if isinstance(payload, dict):
                        for key, val in payload.items():
                            if isinstance(val, dict) and val.get('__typename') == 'Business':
                                if not data['name']:
                                    data['name'] = val.get('name')
                                    data['rating'] = val.get('rating')
                                    data['review_count'] = val.get('reviewCount')
                                    data['phone'] = val.get('phoneNumber')
                                    data['price'] = val.get('priceRange')
                                    enc_biz_id = val.get('encid')
                                    
                                    # Location
                                    loc = val.get('location', {})
                                    if loc:
                                        if isinstance(loc, dict):
                                            addr = loc.get('address', {})
                                            if isinstance(addr, dict):
                                                 data['location'] = addr.get('formattedAddress') or f"{addr.get('streetAddress', '')}, {addr.get('city', '')}, {addr.get('state', '')}"
                                            else:
                                                 data['location'] = loc.get('formattedAddress')
                                    
                                    cats = val.get('categories', [])
                                    if cats and isinstance(cats, list):
                                        data['categories'] = []
                                        for c in cats:
                                            if isinstance(c, dict):
                                                 title = c.get('title')
                                                 if title:
                                                     data['categories'].append(title)
                except:
                    continue

             # Fallback OG
            if not data['name']:
                 og_title = re.search(r'<meta property="og:title" content="([^"]+)"', content)
                 if og_title:
                     data['name'] = og_title.group(1)
                 og_image = re.search(r'<meta property="og:image" content="([^"]+)"', content)
                 if og_image:
                     data['photos'].append(og_image.group(1))
            
            # CRAWLEE FALLBACK
            crawlee_cookies = None
            if not data['name'] and CRAWLEE_AVAILABLE:
                # Primary failed, try Crawlee
                crawlee_result = scrape_with_crawlee(url)
                if crawlee_result and crawlee_result.get('content'):
                    content = crawlee_result['content']
                    crawlee_cookies = crawlee_result.get('cookies')
                    
                    # Re-run hydration parsing on new content
                    scripts = re.findall(r'<script[^>]*type=\"application/json\"[^>]*>(.*?)</script>', content, re.DOTALL)
                    for script_content in scripts:
                        try:
                            clean_content = script_content.replace('<!--', '').replace('-->', '')
                            json_str = html.unescape(clean_content)
                            payload = json.loads(json_str)
                            if isinstance(payload, dict):
                                for key, val in payload.items():
                                    if isinstance(val, dict) and val.get('__typename') == 'Business':
                                         if not data['name']:
                                             data['name'] = val.get('name')
                                             data['rating'] = val.get('rating')
                                             data['review_count'] = val.get('reviewCount')
                                             data['phone'] = val.get('phoneNumber')
                                             data['price'] = val.get('priceRange')
                                             enc_biz_id = val.get('encid')
                                             
                                             loc = val.get('location', {})
                                             if loc:
                                                 if isinstance(loc, dict):
                                                     addr = loc.get('address', {})
                                                     if isinstance(addr, dict):
                                                          data['location'] = addr.get('formattedAddress') or f"{addr.get('streetAddress', '')}, {addr.get('city', '')}, {addr.get('state', '')}"
                                                     else:
                                                          data['location'] = loc.get('formattedAddress')
                                             
                                             cats = val.get('categories', [])
                                             if cats and isinstance(cats, list):
                                                 data['categories'] = []
                                                 for c in cats:
                                                     if isinstance(c, dict):
                                                          title = c.get('title')
                                                          if title:
                                                              data['categories'].append(title)
                        except:
                            continue

            # 2. GraphQL Call for Details (Hours, High-Res Photos)
            if enc_biz_id:
                # If we have Crawlee cookies, use the requests fallback
                if crawlee_cookies:
                     print(f"Found encBizId: {enc_biz_id}, fetching details via requests fallback...")
                     details = get_details_via_requests(enc_biz_id, url, crawlee_cookies)
                else:
                    # Normal flow via browser context
                    print(f"Found encBizId: {enc_biz_id}, fetching details via internal fetch...")
                    details = get_details_via_browser(page, enc_biz_id)

                if details:
                    if details.get('hours'): data['hours'] = details['hours']
                    if details.get('photos'): data['photos'] = details['photos'] + data['photos']
                    if details.get('reviews'): data['reviews'] = details['reviews']
                    if not data['location'] and details.get('location'): data['location'] = details['location']
                    if not data['rating'] and details.get('rating'): data['rating'] = details['rating']
            
            # 3. Menu Items
            slug = url.split('/biz/')[-1].split('?')[0]
            menu_url = f"https://www.yelp.com/menu/{slug}"
            data['menu_url'] = menu_url
            
            print(f"Fetching menu from {menu_url}...")
            # Navigate to menu page
            page.goto(menu_url)
            time.sleep(1) # short wait for render
            
            # Use specific selectors directly in browser is safer than regex on content
            # But converting our BS4/regex logic to Playwright locators is easy
            
            menu_items = page.evaluate("""() => {
                const items = [];
                document.querySelectorAll('.menu-item-details').forEach(div => {
                    const item = {};
                    const titleEl = div.querySelector('h4');
                    if (titleEl) item.name = titleEl.innerText.trim();
                    
                    const descEl = div.querySelector('.menu-item-details-description');
                    if (descEl) item.description = descEl.innerText.trim();
                    
                    // Price is tricky, looking at sibling/parent
                    // Try looking for price in parent container
                    const parent = div.parentElement;
                    if (parent) {
                        const priceEl = parent.querySelector('.menu-item-price-amount');
                        if (priceEl) item.price = priceEl.innerText.trim();
                    }
                    
                    if (item.name) items.push(item);
                });
                return items;
            }""")
            
            data['menu_items'] = menu_items
            
            browser.close()
            
    except Exception as e:
        data['error'] = str(e)
        print(f"Scraper Error: {e}")
        
    return data

def get_details_via_browser(page, enc_biz_id):
    """
    Executes the fetching of details inside the browser context using window.fetch.
    """
    gq_query = {
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
    }
    
    # We execute fetch in the page context
    try:
        result = page.evaluate(f"""async (payload) => {{
            const res = await fetch("https://www.yelp.com/gql/batch", {{
                method: "POST",
                headers: {{
                    "content-type": "application/json",
                    "x-apollo-operation-name": "GetLocalBusinessJsonLinkedData"
                }},
                body: JSON.stringify([payload])
            }});
            return await res.json();
        }}""", gq_query) # Passing python dict, playwright serializes it to JS object
        
        # Parse result (same logic as before)
        if isinstance(result, list) and len(result) > 0:
            biz_data = result[0].get('data', {}).get('business', {})
            parsed = {
                'hours': [],
                'photos': [],
                'reviews': [],
                'location': None,
                'rating': biz_data.get('rating')
            }
            
            # Hours
            hours = biz_data.get('operationHours', {}).get('regularHoursMergedWithSpecialHoursForCurrentWeek', [])
            for h in hours:
                day = h.get('dayOfWeekShort')
                times = h.get('regularHours', [])
                if day and times:
                    parsed['hours'].append(f"{day}: {', '.join(times)}")
            
            # Photos
            media_edges = biz_data.get('media', {}).get('orderedMediaItems', {}).get('edges', [])
            for edge in media_edges:
                node = edge.get('node', {})
                enc_id = node.get('encid')
                if enc_id:
                    parsed['photos'].append(f"https://s3-media0.fl.yelpcdn.com/bphoto/{enc_id}/l.jpg")
            
            # Reviews
            reviews_data = biz_data.get('reviews', {}).get('edges', [])
            for edge in reviews_data:
                node = edge.get('node', {})
                review = {
                    'author': node.get('author', {}).get('displayName', ''),
                    'rating': node.get('rating'),
                    'text': node.get('text', {}).get('full', '') or node.get('text', ''),
                    'date': node.get('localizedDate', '')
                }
                if review['text'] and review['author']:
                    parsed['reviews'].append(review)
            
            return parsed
            
    except Exception as e:
        print(f"GQL Error: {e}")
        return None
    return None


async def _crawlee_fetch(url):
    """
    Internal async function to fetch content using Crawlee.
    Returns dict with 'content' and 'cookies'.
    """
    result = {'content': '', 'cookies': {}}
    
    crawler = PlaywrightCrawler(
        # Automatically enables anti-blocking fingerprints
        browser_pool_options={"use_fingerprints": True},
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
        
        # Extract cookies
        cookies = await context.context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        result['cookies'] = cookie_dict

    await crawler.run([url])
    return result

def scrape_with_crawlee(url):
    """
    Synchronous wrapper for Crawlee fetch
    """
    if not CRAWLEE_AVAILABLE:
        print("Crawlee not installed, skipping fallback.")
        return None
        
    try:
        print(f"Fallback: Fetching {url} with Crawlee...")
        return asyncio.run(_crawlee_fetch(url))
    except Exception as e:
        print(f"Crawlee Error: {e}")
        return None



def get_details_via_requests(enc_biz_id, referer_url, cookies):
    """
    Fallback: Fetches details using requests + harvested keys/cookies.
    """
    url = "https://www.yelp.com/gql/batch"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://www.yelp.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": referer_url,
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.65", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.65"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "x-apollo-operation-name": "GetLocalBusinessJsonLinkedData"
    }

    payload = [
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
        }
    ]

    try:
        response = requests.post(url, headers=headers, json=payload, cookies=cookies, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                biz_data = data[0].get('data', {}).get('business', {})
                
                result = {
                    'hours': [],
                    'photos': [],
                    'location': None,
                    'rating': biz_data.get('rating')
                }
                
                # Hours
                hours = biz_data.get('operationHours', {}).get('regularHoursMergedWithSpecialHoursForCurrentWeek', [])
                for h in hours:
                    day = h.get('dayOfWeekShort')
                    times = h.get('regularHours', [])
                    if day and times:
                         time_str = ", ".join(times)
                         result['hours'].append(f"{day}: {time_str}")
                
                # Photos
                media_edges = biz_data.get('media', {}).get('orderedMediaItems', {}).get('edges', [])
                for edge in media_edges:
                    node = edge.get('node', {})
                    enc_id = node.get('encid')
                    if enc_id:
                        result['photos'].append(f"https://s3-media0.fl.yelpcdn.com/bphoto/{enc_id}/l.jpg")
                
                return result
                
    except Exception as e:
        print(f"Details Fallback Error: {e}")
        return None
    return None

if __name__ == '__main__':

    # Test
    # result = scrape_yelp_business('the-salty-pineapple-herriman-2')
    # print(json.dumps(result, indent=4))
    pass
