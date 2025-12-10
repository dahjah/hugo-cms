from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class SocialLink:
    platform: str
    url: str

@dataclass
class MenuItem:
    name: str
    description: str = ""
    price: str = ""
    image_url: str = ""
    category: str = ""

@dataclass
class Review:
    author: str
    rating: float
    text: str
    date: str = ""
    platform: str = "yelp"

@dataclass
class BusinessProfile:
    """
    Unified representation of a business, aggregated from multiple sources.
    This object is the "Source of Truth" for the site generator.
    """
    # Core Identity
    name: str = ""
    slug: str = ""
    tagline: str = ""
    description: str = ""  # Rich text or HTML
    
    # Visuals
    logo_url: str = ""
    hero_image_url: str = ""
    hero_image_local_path: str = "" # Path relative to media root
    gallery_images: List[str] = field(default_factory=list)
    
    # Aesthetics
    colors: Dict[str, str] = field(default_factory=dict) # { 'primary': '#...', ... }
    colors_css: str = "" # Generated CSS block
    
    # Contact & Location
    phone: str = ""
    email: str = ""
    address: str = "" # Full formatted address
    location_str: str = "" # Short "City, ST"
    geo_lat: Optional[float] = None
    geo_lng: Optional[float] = None
    
    # Operational
    hours: List[str] = field(default_factory=list)
    price_level: str = "" # "$", "$$", etc
    categories: List[str] = field(default_factory=list)
    
    # Content
    menu_items: List[MenuItem] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    social_links: List[SocialLink] = field(default_factory=list)
    
    # Stats (followers, likes, etc. - platform specific)
    stats: Dict[str, int] = field(default_factory=dict)  # {'followers': 1000, 'likes': 500}
    
    # Metadata
    website_url: str = ""
    booking_url: str = ""
    
    def merge(self, other: 'BusinessProfile'):
        """
        Merge another profile into this one, preferring non-empty values from 'other'.
        """
        for field_name in self.__dataclass_fields__:
            value = getattr(other, field_name)
            current = getattr(self, field_name)
            
            # Simple overwrite if new value exists and current is empty
            if value and not current:
                setattr(self, field_name, value)
            
            # Lists: Extend if source has items
            elif isinstance(value, list) and value:
                current.extend(value)
                
    def to_dict(self) -> dict:
        """Convert to dict for template population."""
        from dataclasses import asdict
        return asdict(self)
