import requests
import colorgram
import os
import tempfile
from typing import List, Dict, Tuple

def sort_colors(colors: List[colorgram.Color]) -> List[Tuple[int, int, int]]:
    """
    Sort extracted colors into a logical palette:
    1. Primary: Most dominant (excluding white/black)
    2. Secondary: Second most dominant
    3. Accent: Highest saturation
    4. Background: Lightest
    5. Text: Darkest
    """
    # Helper to convert to (r,g,b) tuple
    rgb_colors = [(c.rgb.r, c.rgb.g, c.rgb.b) for c in colors]
    
    # Helper to get saturation (approximated)
    def get_saturation(rgb):
        r, g, b = rgb
        mx = max(r, g, b)
        mn = min(r, g, b)
        return (mx - mn) / (mx or 1)
        
    # Helper to get luminance
    def get_luminance(rgb):
        r, g, b = rgb
        return (0.299*r + 0.587*g + 0.114*b)

    # Filter out near-whites and near-blacks for Primary/Secondary candidates
    candidates = []
    for rgb in rgb_colors:
        lum = get_luminance(rgb)
        if 20 < lum < 235: # Ignore pure whites and blacks
            candidates.append(rgb)
            
    # Default to raw list if filtering removed everything
    if not candidates:
        candidates = rgb_colors

    # 1. Primary: Most prominent candidate
    primary = candidates[0] if candidates else (0, 0, 0)
    
    # 2. Secondary: Second candidate, or complement
    secondary = candidates[1] if len(candidates) > 1 else (50, 50, 50)
    
    # 3. Accent: Most saturated from full list
    accent = max(rgb_colors, key=get_saturation)
    
    # 4. Background: Lightest from full list (or generic off-white)
    bg_candidate = max(rgb_colors, key=get_luminance)
    bg = bg_candidate if get_luminance(bg_candidate) > 200 else (250, 250, 250)
    
    # 5. Text: Darkest from full list (or generic off-black)
    text_candidate = min(rgb_colors, key=get_luminance)
    text = text_candidate if get_luminance(text_candidate) < 50 else (30, 30, 30)

    return [primary, secondary, accent, bg, text]

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def extract_colors_from_path(file_path: str, num_colors: int = 10) -> str:
    """
    Extracts CSS palette from a local file path.
    """
    try:
        colors = colorgram.extract(file_path, num_colors)
        if not colors:
            return ""
            
        palette = sort_colors(colors)
        
        css = ":root {\n"
        names = ['primary', 'secondary', 'accent', 'bg', 'text']
        
        for name, rgb in zip(names, palette):
            css += f"    --color-{name}: {rgb_to_hex(rgb)};\n"
            
        # Generate some derivatives for full theme support
        css += f"    --color-muted: {rgb_to_hex(palette[1])}80;\n" # 50% opacity secondary
        css += f"    --color-border: {rgb_to_hex(palette[4])}20;\n" # 12% opacity text
        
        css += "}\n"
        return css
    except Exception as e:
        print(f"Color Extraction Error: {e}")
        return ""

def extract_colors_from_url(image_url: str) -> str:
    """
    Downloads image and extracts a CSS variable block.
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
            
        css = extract_colors_from_path(tmp_path)
        os.remove(tmp_path)
        return css
        
    except Exception as e:
        print(f"Download Error: {e}")
        return ""

if __name__ == '__main__':
    # Test
    url = "https://s3-media0.fl.yelpcdn.com/bphoto/HpkAjvygZed_c914j9P6hw/l.jpg"
    print(extract_colors_from_url(url))
