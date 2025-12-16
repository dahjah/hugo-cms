from django.db import models
from django.db.models import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
from .deployment_models import DeploymentProvider
from taggit.managers import TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase, TaggedItemBase

class BlockDefinition(models.Model):
    """
    Defines the schema for a component (e.g., 'Hero', 'YouTube').
    """
    id = models.CharField(max_length=50, primary_key=True, help_text="Unique key like 'hero' or 'youtube'")
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Lucide icon name (e.g., 'layout')")
    has_visual_preview = models.BooleanField(default=False, help_text="Does the frontend have a specific renderer for this?")
    is_container = models.BooleanField(default=False, help_text="Can this block contain other blocks?")
    schema = JSONField(default=dict, help_text="JSON Schema defining the fields (title, type, default, etc.)")
    default_params = JSONField(default=dict, help_text="Default values when a user drags this block in")

    def __str__(self):
        return self.label

class Website(models.Model):
    """
    Represents a distinct website managed by the CMS.
    """
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('cupcake', 'Cupcake'),
        ('corporate', 'Corporate'),
        ('retro', 'Retro'),
        ('cyberpunk', 'Cyberpunk'),
        ('valentine', 'Valentine'),
        ('halloween', 'Halloween'),
        ('garden', 'Garden'),
        ('forest', 'Forest'),
        ('aqua', 'Aqua'),
        ('lofi', 'Lo-Fi'),
        ('pastel', 'Pastel'),
        ('fantasy', 'Fantasy'),
        ('wireframe', 'Wireframe'),
        ('black', 'Black'),
        ('luxury', 'Luxury'),
        ('dracula', 'Dracula'),
        ('cmyk', 'CMYK'),
        ('autumn', 'Autumn'),
        ('business', 'Business'),
        ('acid', 'Acid'),
        ('lemonade', 'Lemonade'),
        ('night', 'Night'),
        ('coffee', 'Coffee'),
        ('winter', 'Winter'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True, help_text="URL slug for the website (e.g., 'my-site')")
    custom_css = models.TextField(blank=True, null=True, help_text="Global CSS for the website")
    deployment_provider = models.ForeignKey('DeploymentProvider', on_delete=models.SET_NULL, null=True, blank=True, related_name='websites', help_text="Deployment configuration for this website")
    theme_preset = models.CharField(max_length=50, choices=THEME_CHOICES, default="light", help_text="DaisyUI theme for the website")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Page(models.Model):
    """
    Represents a single URL/Page in the Hugo site.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='pages', null=True, blank=True)
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, help_text="URL path (e.g., '/about')")
    layout = models.CharField(max_length=100, default='single', help_text="Hugo layout template name")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Hugo Metadata
    date = models.DateField(blank=True, null=True) 
    description = models.TextField(blank=True)
    tags = JSONField(default=list, blank=True, help_text="List of strings")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_published_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last successful publish")

    def __str__(self):
        return f"{self.title} ({self.slug})"

class LayoutTemplate(models.Model):
    """
    Defines a page layout template (e.g., 'home', 'single', 'list').
    Controls which zones are available for a given page.
    """
    id = models.CharField(max_length=50, primary_key=True, help_text="Unique key like 'home' or 'list'")
    label = models.CharField(max_length=100, help_text="Human-readable name like 'Home Page'")
    zones = JSONField(
        default=list, 
        help_text="Array of zone configs: [{'name': 'header', 'width': 'w-full', 'order': 0, 'cssClasses': ''}]. "
                  "Supported widths: 'w-64' (fixed), 'flex-1' (flexible), 'w-full' (full width). "
                  "Order controls display sequence in flex container."
    )
    description = models.TextField(blank=True, help_text="Optional description for admin UI")
    
    class Meta:
        ordering = ['label']
    
    def __str__(self):
        return self.label

class BlockInstance(models.Model):
    """
    A unified model for all blocks (top-level and nested).
    Hierarchy is determined by the 'parent' field.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='blocks', null=True, blank=True)
    definition = models.ForeignKey(BlockDefinition, on_delete=models.CASCADE, related_name='instances')
    
    # --- HIERARCHY FIELDS ---
    
    # 1. Page Link (Only used for top-level blocks in the 'main' zone)
    page = models.ForeignKey(
        Page, 
        on_delete=models.CASCADE, 
        related_name='main_blocks', 
        null=True, 
        blank=True,
        help_text="Link to Page if this is a main content block."
    )
    
    # 2. Self-Referential Link (Used for nested blocks OR global 'header'/'footer' blocks)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        related_name='children', 
        null=True, 
        blank=True,
        help_text="Link to the parent block (e.g., a 'flex_columns' instance)."
    )

    # 3. Zone/Column Identifier (Determines placement)
    placement_key = models.CharField(
        max_length=50, 
        help_text="The zone ('header'/'footer') or column key ('col_1', 'col_2') it belongs to."
    )
    
    # --- CONTENT FIELDS ---

    sort_order = models.PositiveIntegerField(default=0)
    params = JSONField(default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['page', 'placement_key', 'sort_order']),
            models.Index(fields=['parent', 'placement_key', 'sort_order']),
        ]
        
    def __str__(self):
        parent_info = f"Parent: {self.parent.id}" if self.parent else "No Parent"
        return f"{self.definition.id} ({self.placement_key}) - {parent_info}"

class UploadedFile(models.Model):
    """
    Represents a file uploaded by the user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, help_text="Relative path in storage")
    file_url = models.CharField(max_length=500, help_text="Publicly accessible URL")
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

class StorageSettings(models.Model):
    """
    Configuration for file storage (Local or S3).
    """
    STORAGE_TYPES = [
        ('local', 'Local Filesystem'),
        ('s3', 'S3 Compatible Storage'),
    ]

    website = models.OneToOneField(Website, on_delete=models.CASCADE, related_name='storage_settings')
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPES, default='local')

    # S3 Settings
    s3_bucket = models.CharField(max_length=200, blank=True)
    s3_endpoint = models.CharField(max_length=200, blank=True, help_text="e.g., https://nyc3.digitaloceanspaces.com")
    s3_access_key = models.CharField(max_length=200, blank=True)
    s3_secret_key = models.CharField(max_length=200, blank=True)
    s3_region = models.CharField(max_length=100, blank=True)
    s3_public_url = models.CharField(max_length=200, blank=True, help_text="Base URL for public access (CDN)")

    # Local Settings
    local_media_path = models.CharField(max_length=200, default='media/uploads', help_text="Directory to store files")
    local_public_url = models.CharField(max_length=200, default='/media/', help_text="URL prefix for local files")

    def __str__(self):
        return f"Storage Settings for {self.website.name}"


class TemplateCategory(models.Model):
    """
    Categories for organizing site templates (e.g., Healthcare, Food & Beverage).
    """
    slug = models.CharField(max_length=50, primary_key=True, help_text="URL-friendly identifier")
    name = models.CharField(max_length=100, help_text="Display name for the category")
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="Sort order in template gallery")

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Template Categories"

    def __str__(self):
        return self.name


class CharFieldTaggedItem(TaggedItemBase):
    """
    Custom TaggedItem that uses CharField for object_id to support SiteTemplate's CharField PK.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_tagged_items"
    )
    object_id = models.CharField(max_length=50, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Tagged Item"
        verbose_name_plural = "Tagged Items"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]


class TemplateTag(models.Model):
    """
    Controlled vocabulary for template tags.
    Used for autocomplete and LLM matching. Templates store tag names in JSONField.
    """
    name = models.SlugField(max_length=50, primary_key=True, help_text="Slug-style tag name (e.g., 'therapy', 'food-truck')")
    label = models.CharField(max_length=100, help_text="Human-readable label")
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['label']
    
    def __str__(self):
        return self.label


class SiteTemplate(models.Model):
    """
    Predefined site templates that users can import to create new websites.
    Contains serialized pages, blocks, and CSS that can be applied to a new website.
    Tags are used for LLM template selection based on industry/business type.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=50, unique=True, help_text="URL-friendly identifier (e.g., 'modern-therapist', 'food-truck-basic')")
    name = models.CharField(max_length=100, help_text="Display name for the template")
    description = models.TextField(blank=True)
    thumbnail_url = models.CharField(max_length=500, blank=True, help_text="Preview image URL")
    
    # Tags for LLM selection (simple JSON array - works with SQLite)
    # Use TemplateTag model for autocomplete/controlled vocabulary
    tags = JSONField(default=list, help_text="List of tag names for template categorization and LLM selection")

    theme_preset = models.CharField(max_length=50, default="default", help_text="The theme engine this template is optimized for.")
    
    # Serialized template content
    base_css = models.TextField(blank=True, help_text="CSS variables and base styles")
    pages_json = JSONField(
        default=list, 
        help_text="Serialized pages with blocks: [{slug, title, layout, blocks: [...]}]"
    )
    
    # Placeholder schema for LLM content filling
    placeholder_schema = JSONField(
        default=dict,
        help_text="Schema defining placeholders LLM should fill: {business_name: 'text', tagline: 'text', ...}"
    )
    
    # Metadata
    created_by = models.CharField(max_length=100, blank=True, help_text="Attribution for template creator")
    is_featured = models.BooleanField(default=False, help_text="Show prominently in template gallery")
    is_public = models.BooleanField(default=True, help_text="Available to all users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name