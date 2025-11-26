from django.db import models
from django.db.models import JSONField  # Standard Django JSONField (uses JSONB on Postgres)
from django.core.serializers.json import DjangoJSONEncoder
import uuid

class BlockDefinition(models.Model):
    """
    Defines the schema for a component (e.g., 'Hero', 'YouTube').
    This allows the backend to tell the frontend what blocks are available.
    """
    id = models.CharField(max_length=50, primary_key=True, help_text="Unique key like 'hero' or 'youtube'")
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Lucide icon name (e.g., 'layout')")
    has_visual_preview = models.BooleanField(default=False, help_text="Does the frontend have a specific renderer for this?")
    default_params = JSONField(default=dict, help_text="Default values when a user drags this block in")

    def __str__(self):
        return self.label

class Page(models.Model):
    """
    Represents a single URL/Page in the Hugo site.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True, help_text="URL path (e.g., '/about')")
    layout = models.CharField(max_length=100, default='single', help_text="Hugo layout template name")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Hugo Metadata
    date = models.DateField(blank=True, null=True) # Changed to allow null for flexibility
    description = models.TextField(blank=True)
    tags = JSONField(default=list, blank=True, help_text="List of strings")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.slug})"

class BlockInstance(models.Model):
    """
    An actual instance of a block content.
    Can be attached to a Page (zone='main') OR be global (page=null, zone='header'/'footer').
    """
    ZONE_CHOICES = [
        ('header', 'Global Header'),
        ('main', 'Page Main Content'),
        ('footer', 'Global Footer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definition = models.ForeignKey(BlockDefinition, on_delete=models.CASCADE, related_name='instances')
    
    # Relationship logic: 
    # If zone='main', 'page' must be set.
    # If zone='header'/'footer', 'page' should be null (global).
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='blocks', null=True, blank=True)
    zone = models.CharField(max_length=20, choices=ZONE_CHOICES)
    
    sort_order = models.PositiveIntegerField(default=0)
    
    # The actual content (title, image src, markdown text, etc.)
    params = JSONField(default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['page', 'zone']),
            models.Index(fields=['zone']),
        ]

    def __str__(self):
        return f"{self.definition.id} in {self.zone} ({self.id})"