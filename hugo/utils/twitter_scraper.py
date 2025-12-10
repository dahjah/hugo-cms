import requests
import re
import json
import html

def scrape_twitter_profile(username):
    """
    Scrape basic profile info from a public Twitter/X profile.
    Uses 'Slackbot-LinkExpanding' User-Agent to encourage server-side rendering
    of Open Graph tags (og:title, og:description, og:image).
    """
    # Handle @ prefix
    if username.startswith('@'):
        username = username[1:]
        
    url = f"https://x.com/{username}"
    
    # Specific UA that often gets hydration/meta tags for link previews
    headers = {
        'User-Agent': 'Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    data = {
        'username': username,
        'screen_name': '',
        'name': '',
        'profile_pic_url': '',
        'biography': '',
        'external_url': '',
        'followers': 0,
        'following': 0,
        'tweets': []
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # response.raise_for_status() # Soft fail preferred
        
        content = response.text
        
        # Extract OG Tags
        def get_meta_property(prop_name):
            # Matches <meta property="prop_name" content="value" /> or variations
            match = re.search(r'<meta\s+(?:property|name)=["\']' + re.escape(prop_name) + r'["\']\s+content=["\']([^"\']+)["\']', content)
            if match:
                return html.unescape(match.group(1))
            # Try reversed attribs: content="..." property="..."
            match_rev = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']' + re.escape(prop_name) + r'["\']', content)
            if match_rev:
                return html.unescape(match_rev.group(1))
            return ''

        # 1. Name & Screen Name from Title
        # Format: "Name (@screen_name) on X"
        og_title = get_meta_property('og:title')
        if og_title:
            data['name'] = og_title
            # Try to parse out stats if possible, but title is usually just Name
            # Regex for "Name (@handle) on X"
            name_match = re.match(r'(.*?) \(@(.*?)\) on X', og_title)
            if name_match:
                data['name'] = name_match.group(1)
                data['screen_name'] = name_match.group(2)
        
        # 2. Bio from Description
        # OG Description usually contains the Bio
        data['biography'] = get_meta_property('og:description')
        
        # 3. Avatar from OG Image
        data['profile_pic_url'] = get_meta_property('og:image')
        
        # 4. Attempt to parse stats from description? 
        # Sometimes description is "The latest Tweets from...". 
        # But usually it's the user bio.
        # Stats are notoriously hard to get from static metatags on X.
        
    except Exception as e:
        data['error'] = str(e)
        
    return data

if __name__ == '__main__':
    # Test
    result = scrape_twitter_profile('elonmusk')
    print(json.dumps(result, indent=4))
