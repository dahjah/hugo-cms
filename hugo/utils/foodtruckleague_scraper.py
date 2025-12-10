import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def scrape_food_truck(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract name and subtitle
        name_tag = soup.find('h2', class_='font-bold')
        name = name_tag.get_text(strip=True) if name_tag else 'N/A'
        
        subtitle_tag = soup.find('div', class_='my-10')
        subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else 'N/A'

        # Extract bio/story
        story = 'N/A'
        story_div = soup.find('div', class_='relative mb-10')
        if story_div:
            p_tag = story_div.find('p')
            if p_tag:
                story = p_tag.get_text(strip=True)

        # Extract images and convert to absolute URLs
        images = []
        img_tags = soup.find_all('img', src=True)
        for img in img_tags:
            src = img['src']
            alt = img.get('alt', '')
            if 'truckLogo' in alt or 'cdn.files.smartsuite.com' in src:
                absolute_url = urljoin(url, src)
                images.append(absolute_url)

        # Extract booking link
        book_button = soup.find('button', string='Book this truck')
        book_url = 'N/A'
        if book_button:
            parent_link = book_button.find_parent('a')
            if parent_link and parent_link.get('href'):
                book_url = urljoin(url, parent_link['href'])

        # Build JSON output
        result = {
            'name': name,
            'subtitle': subtitle,
            'bio': story,
            'images': images,
            'book_link': book_url
        }

        return json.dumps(result, indent=4)
        
    except Exception as e:
        return json.dumps({'error': str(e)}, indent=4)

if __name__ == '__main__':
    # Test with the provided URL
    url = 'https://foodtruckleague.com/Utah/trucks/677ec632f7fd49c21152b236'
    print(scrape_food_truck(url))
