import requests
import json
import re

def scrape_tiktok_profile(username):
    """
    Scrape basic profile info and recent videos from a TikTok public profile.
    Uses regex to extract the __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON blob.
    
    Returns:
        dict: Standardized profile data (username, avatar, bio, stats, videos)
    """
    # Handle @ prefix if present
    if not username.startswith('@'):
        url_username = f"@{username}"
    else:
        url_username = username
        username = username[1:]
        
    url = f"https://www.tiktok.com/{url_username}?lang=en"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.tiktok.com/',
    }
    
    data = {
        'username': username,
        'profile_pic_url': '',
        'biography': '',
        'external_url': '',
        'followers': 0,
        'following': 0,
        'likes': 0,
        'videos': []
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        content = response.text
        
        # Look for the hydration script
        script_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', content, re.DOTALL)
        
        if script_match:
            try:
                json_str = script_match.group(1)
                universal_data = json.loads(json_str)
                
                # Navigate the deeply nested structure
                # Typically: __DEFAULT_SCOPE__ -> "webapp.user-detail" -> userInfo
                default_scope = universal_data.get('__DEFAULT_SCOPE__', {})
                user_detail = default_scope.get('webapp.user-detail', {})
                
                # User Info
                user_info = user_detail.get('userInfo', {})
                user = user_info.get('user', {})
                stats = user_info.get('stats', {})
                
                data['secUid'] = user.get('secUid')
                data['profile_pic_url'] = user.get('avatarLarger') or user.get('avatarMedium')
                data['biography'] = user.get('signature')
                data['external_url'] = user.get('bioLink', {}).get('link')
                data['followers'] = stats.get('followerCount')
                data['following'] = stats.get('followingCount')
                data['likes'] = stats.get('heartCount')
                
                # Try to extract videos from Universal Data
                # Often in default_scope under 'webapp.video-detail' or similar if loaded, 
                # but usually universal data just has user info unless we look deep.
                # Actually, sometimes it's simpler:
                # Look for any key that holds a list of items
            except:
                pass

        # Fallback/Alternative: SIGI_STATE
        sigi_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', content)
        if sigi_match:
            try:
                sigi_data = json.loads(sigi_match.group(1))
                user_module = sigi_data.get('UserModule', {})
                users = user_module.get('users', {})
                
                # If we didn't get user info yet, get it here
                if not data['username'] and users:
                    # Just take the first one or match
                    username_key = next(iter(users))
                    user = users[username_key]
                    
                    data['username'] = user.get('uniqueId')
                    data['profile_pic_url'] = user.get('avatarLarger')
                    data['biography'] = user.get('signature')
                    
                    stats = user_module.get('stats', {}).get(username_key, {})
                    data['followers'] = stats.get('followerCount')
                    data['following'] = stats.get('followingCount')
                    data['likes'] = stats.get('heartCount')

                # Video extraction from SIGI_STATE
                item_module = sigi_data.get('ItemModule', {})
                for item_id, item in item_module.items():
                    video = {
                        'id': item.get('id'),
                        'desc': item.get('desc'),
                        'createTime': item.get('createTime'),
                        'cover': item.get('video', {}).get('cover'),
                        'playAddr': item.get('video', {}).get('playAddr'),
                        'stats': item.get('stats', {})
                    }
                    data['videos'].append(video)
            except:
                pass

    except Exception as e:
        data['error'] = str(e)
        
    return data

if __name__ == '__main__':
    # Test
    result = scrape_tiktok_profile('strippindippinchicken')
    print(json.dumps(result, indent=4))
