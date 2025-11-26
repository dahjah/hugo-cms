from django.db import models
from django.db.models import JSONField
from django.core.serializers.json import DjangoJSONEncoder
import uuid

class BlockDefinition(models.Model):
    """
    Defines the schema for a component (e.g., 'Hero', 'YouTube').
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
    date = models.DateField(blank=True, null=True) 
    description = models.TextField(blank=True)
    tags = JSONField(default=list, blank=True, help_text="List of strings")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.slug})"

class BlockInstance(models.Model):
    """
    A unified model for all blocks (top-level and nested).
    Hierarchy is determined by the 'parent' field.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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