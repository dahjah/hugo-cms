#!/usr/bin/env python3
"""
Fix remaining {{placeholder}} strings in HTML content
"""
import re

# Read the file
with open('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms/bin/create_sample_templates.py', 'r') as f:
    content = f.read()

# Replace all {{...}} patterns in HTML content strings
# This is more aggressive - catches placeholders embedded in HTML
content = re.sub(r'\{\{[^}]+\}\}', '', content)

# Write back
with open('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms/bin/create_sample_templates.py', 'w') as f:
    f.write(content)

print("✅ Removed ALL remaining {{...}} placeholders including those in HTML")
