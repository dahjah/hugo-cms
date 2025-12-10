"""
Base Scraper Abstract Class

All scrapers should extend this class and implement the required classmethods.
Pattern:
    context = MyScraper.connect("identifier")
    profile = MyScraper.scrape(context)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, ClassVar
from hugo.schemas import BusinessProfile


@dataclass
class ScraperContext:
    """
    Connection context returned by connect().
    Contains everything needed to execute the scrape.
    """
    identifier: str              # Original input (URL, username, slug)
    normalized_id: str           # Cleaned identifier (e.g., just the slug)
    platform: str                # Which platform this context is for
    
    # Auth & Connection
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    api_key: Optional[str] = None
    
    # Platform-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Connection state
    is_valid: bool = True
    error: Optional[str] = None


class BaseScraper(ABC):
    """
    Abstract base class for all platform scrapers.
    
    All methods are classmethods - no instantiation required.
    
    Usage:
        from hugo.scrapers.yelp import YelpScraper
        
        ctx = YelpScraper.connect("the-salty-pineapple-herriman-2")
        if ctx.is_valid:
            profile = YelpScraper.scrape(ctx)
    """
    
    # Class-level attributes to be overridden
    platform: ClassVar[str] = "unknown"
    
    # Which BusinessProfile fields this scraper can populate
    supported_fields: ClassVar[Set[str]] = set()
    
    @classmethod
    @abstractmethod
    def can_handle(cls, identifier: str) -> bool:
        """
        Return True if this scraper can handle the given URL/identifier.
        Used for auto-detection in the orchestrator.
        """
        pass
    
    @classmethod
    @abstractmethod
    def connect(cls, identifier: str) -> ScraperContext:
        """
        Validate the identifier and prepare connection context.
        
        Returns ScraperContext with:
        - normalized_id: cleaned identifier
        - headers/cookies: any auth or session data
        - metadata: platform-specific extras
        - is_valid: False if connection failed
        - error: error message if is_valid is False
        """
        pass
    
    @classmethod
    @abstractmethod
    def scrape(cls, context: ScraperContext) -> BusinessProfile:
        """
        Execute the scrape using the provided context.
        
        Args:
            context: ScraperContext from connect()
        
        Returns:
            BusinessProfile with populated fields
        """
        pass
    
    @classmethod
    def scrape_url(cls, identifier: str) -> BusinessProfile:
        """
        Convenience method: connect + scrape in one call.
        """
        ctx = cls.connect(identifier)
        if not ctx.is_valid:
            raise ValueError(f"Connection failed: {ctx.error}")
        return cls.scrape(ctx)

    @staticmethod
    def _extract_email(text: str) -> str:
        """Helper to extract email from text block."""
        import re
        if not text: return ""
        # Simple regex for email extraction
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return match.group(0) if match else ""
