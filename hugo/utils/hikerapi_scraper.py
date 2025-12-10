import requests
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = "1b42yowz11l52wmybh4x8e2ujp4kj49g"
API_BASE = "https://api.hikerapi.com"
HEADERS = {"x-access-key": API_KEY}

def scrape_instagram_profile_hikerapi(username):
    """
    Scrape Instagram profile using HikerAPI
    Returns standardized dict similar to the meta-tag scraper
    """
    logger.info(f"Fetching HikerAPI data for @{username}...")
    
    try:
        response = requests.get(
            f"{API_BASE}/a2/user",
            params={"username": username},
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()
        
        data = response.json()
        user_data = data.get('graphql', {}).get('user', {})
        
        if not user_data:
            return json.dumps({'error': 'No user data found in HikerAPI response'}, indent=4)
            
        # Parse into standard format
        result = {
            'username': user_data.get('username'),
            'profile_pic_url': user_data.get('profile_pic_url_hd'),
            'biography': user_data.get('biography'),
            'external_url': user_data.get('external_url'),
            'followers': user_data.get('edge_followed_by', {}).get('count'),
            'following': user_data.get('edge_follow', {}).get('count'),
            'posts': []
        }
        
        # Get recent posts
        posts = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
        for post in posts[:12]:
            node = post.get('node', {})
            post_data = {
                'id': node.get('id'),
                'type': node.get('__typename'),
                'image_url': node.get('display_url'),
                'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                'likes': node.get('edge_liked_by', {}).get('count'),
                'is_video': node.get('is_video', False)
            }
            result['posts'].append(post_data)
            
        return json.dumps(result, indent=4)
        
    except Exception as e:
        logger.error(f"HikerAPI error: {e}")
        return json.dumps({'error': str(e)}, indent=4)

if __name__ == '__main__':
    # Test with default
    print(scrape_instagram_profile_hikerapi('strippindippinchicken'))
