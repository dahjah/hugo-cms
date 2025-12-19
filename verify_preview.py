
import requests
import json
from django.test import Client
from hugo.models import Website, Page

# Use Django Client to avoid auth hassle + localhost port issues
c = Client()

website_id = '01eb19ad-f554-4057-a09e-262f14c21272'
page_id = '0a35f66b-0654-45ea-9bb3-c92b4053bf20'

print(f"Testing for Website: {website_id}")

# 1. POST render_canvas
payload = {
    'website_id': website_id,
    'page_id': page_id,
    'page': {'slug': '/test-preview'}, # Use a custom slug to test path
    'blocks': []
}

print("Calling render_canvas...")
response = c.post(
    '/api/websites/render_canvas/', 
    data=payload, 
    content_type='application/json'
)

print(f"Render Status: {response.status_code}")
if response.status_code != 200:
    print(response.json())
else:
    print("Render Success:", response.json())

# 2. GET preview asset
# Url: /api/sites/{id}/preview/ (root)
print("Calling serve_preview_asset (ROOT)...")
preview_url = f"/api/sites/{website_id}/preview/"
resp = c.get(preview_url)

print(f"Preview Status: {resp.status_code}")
content = resp.content.decode('utf-8')

if "CMS Editor Connected" in content:
    print("SUCCESS: Editor script found in HTML.")
else:
    print("FAILURE: Editor script NOT found in HTML.")
    print("Snippet:", content[:500])

if f'<base href="/api/sites/{website_id}/preview/">' in content:
     print("SUCCESS: Base tag found.")
else:
     print("FAILURE: Base tag NOT found.")

# Check for rewritten CSS paths
# Expecting: href="/api/sites/.../preview/css/..."
expected_css_path = f'/api/sites/{website_id}/preview/css/'
if expected_css_path in content:
     print(f"SUCCESS: Rewritten CSS path found: {expected_css_path}")
else:
     print(f"FAILURE: Rewritten CSS path NOT found. Expected {expected_css_path}")
     # Find any css link
     if '/css/' in content:
          print("Found other CSS links:")
          import re
          matches = re.findall(r'href=["\'].*?css.*?["\']', content)
          for m in matches:
               print(m)

# 3. Test CSS Fetching
# URL: /api/sites/{id}/preview/css/styles.css
print("\nTesting CSS Fetching...")

# Test styles.css (Should exist)
css_url = f"/api/sites/{website_id}/preview/css/styles.css"
print(f"Fetching {css_url}...")
resp = c.get(css_url)
print(f"styles.css Status: {resp.status_code}")
print(f"styles.css MIME: {resp.get('Content-Type')}")

# Test custom.css (Likely missing based on logs)
custom_css_url = f"/api/sites/{website_id}/preview/css/custom.css"
print(f"Fetching {custom_css_url}...")
resp = c.get(custom_css_url)
print(f"custom.css Status: {resp.status_code}")
print(f"custom.css MIME: {resp.get('Content-Type')}")

