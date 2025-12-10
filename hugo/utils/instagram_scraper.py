import requests
import json
import re

def scrape_instagram_profile(username):
    """
    Scrape basic profile info and recent posts from an Instagram public profile.
    Uses regex to parse meta tags and /embed JSON to avoid heavy dependencies (bs4).
    """
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    data = {
        'username': username,
        'profile_pic_url': '',
        'biography': '',
        'external_url': '',
        'followers': 0,
        'following': 0,
        'posts': []
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        content = response.text
        
        # 1. Parse Meta Tags using Regex (instead of BS4)
        # og:image
        og_image_match = re.search(r'<meta property="og:image" content="([^"]+)"', content)
        if og_image_match:
            data['profile_pic_url'] = og_image_match.group(1)
            
        # og:description for stats
        og_desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
        if og_desc_match:
            desc_content = og_desc_match.group(1)
            # Format usually: "100 Followers, 20 Following, 50 Posts - ..."
            parts = desc_content.split(' - ')
            if parts:
                stats_part = parts[0]
                # Extract numbers
                followers_match = re.search(r'([\d,]+) Followers', stats_part)
                if followers_match:
                    data['followers'] = followers_match.group(1)
                    
                following_match = re.search(r'([\d,]+) Following', stats_part)
                if following_match:
                    data['following'] = following_match.group(1)
            
            if len(parts) > 1:
                data['biography'] = parts[1]

    except Exception as e:
        data['error'] = str(e)

    # 2. Add /embed fallback (often has better image data)
    # Even if main page worked for bio, embed often returns usable media links
    if not data.get('error') or not data['posts']:
        embed_data = scrape_embed_data(username)
        if embed_data:
            # Merge embed data
            if not data['profile_pic_url']:
                data['profile_pic_url'] = embed_data.get('profile_pic_url', '')
            
            # Embed posts are usually high quality, so we can append or replace
            if not data['posts']:
                data['posts'] = embed_data.get('posts', [])
                
    return data



def get_instagram_embed_data(username):
    url = f'https://www.instagram.com/{username}/embed/'
    try:
        content = requests.get(url).text
        match = re.search(r'"contextJSON":\s*(".+}")', content)
        if match:
            return json.loads(
                json.loads(match.group(1))
            ).get('context')
    except Exception as e:
        print(f"Error fetching embed data: {e}")
    
    return {}


def scrape_embed_data(username):
    """
    Attempt to scrape data from the user's embed profile page.
    This often contains a 'contextJSON' blob with useful data.
    """
    
    try:
        # response = requests.get(url, headers=headers)
        # if response.status_code != 200:
        #     return None
            
        # content = response.text
        
        # Regex to find the config JSON blob
        # Look for "contextJSON": followed by a JSON string
        # match = re.search(r'"contextJSON":\s*(".+}")', content)
        # if match:
        # The JSON payload is a double-encoded string literal inside the JS
        # inner_json_str = json.loads(match.group(1))
        # context_data = json.loads(inner_json_str)

        context_data = get_instagram_embed_data(username)
        
        # Extract useful bits
        # Top level keys based on user example: 'followers_count', 'graphql_media', 'profile_pic_url', 'username'
        
        # Map top level fields
        result = {
            'username': context_data.get('username', username),
            'profile_pic_url': context_data.get('profile_pic_url', ''),
            'followers': context_data.get('followers_count', 0),
            'posts': []
        }
        
        # Helper to get caption
        def get_caption(node):
            edges = node.get('edge_media_to_caption', {}).get('edges', [])
            if edges:
                return edges[0].get('node', {}).get('text', '')
            return ''

        # Parse graphql_media
        graphql_media = context_data.get('graphql_media', [])
        for item in graphql_media:
            # Items can be GraphImage or GraphVideo inside 'shortcode_media' or similar keys
            # The user example shows the media object is directly inside 'shortcode_media' key? 
            # Actually user example: 'graphql_media': [{'shortcode_media': {...}}, ...]
            
            media_node = item.get('shortcode_media')
            if not media_node:
                continue
                
            post_data = {
                'id': media_node.get('id'),
                'image_url': media_node.get('display_url'),
                'caption': get_caption(media_node),
                'likes': media_node.get('edge_liked_by', {}).get('count'),
                'is_video': media_node.get('is_video', False),
                'shortcode': media_node.get('shortcode')
            }
            
            # If video, try to get video url if present (user example shows video_url for GraphVideo)
            if post_data['is_video'] and media_node.get('video_url'):
                    post_data['video_url'] = media_node.get('video_url')
                    
            result['posts'].append(post_data)

        return result
            
    except Exception as e:
        # print(f"Embed scrape error: {e}") 
        pass

    return None

if __name__ == '__main__':
    # Test with defaults
    result = scrape_instagram_profile('strippindippinchicken')
    print(json.dumps(result, indent=4))
