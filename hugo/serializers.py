from rest_framework import serializers
from .models import Page, BlockDefinition, BlockInstance, LayoutTemplate, Website

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'name', 'slug']

class BlockDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockDefinition
        fields = ['id', 'label', 'icon', 'has_visual_preview', 'default_params']

class LayoutTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutTemplate
        fields = ['id', 'label', 'zones', 'description']

# --- Recursive Block Serializer ---

class BlockInstanceSerializer(serializers.ModelSerializer):
    # Field to hold nested blocks (children)
    children = serializers.SerializerMethodField()
    # Flatten the type ID
    type = serializers.ReadOnlyField(source='definition.id')
    
    class Meta:
        model = BlockInstance
        # Note: We expose the placement_key and parent_id for tracking
        fields = ['id', 'type', 'params', 'placement_key', 'sort_order', 'parent_id', 'children', 'website']
        read_only_fields = ['id', 'type', 'parent_id'] 

    def get_children(self, obj):
        # Recursively serialize children, ordering by sort_order
        children = obj.children.all().order_by('sort_order')
        # Use the same serializer recursively
        serializer = BlockInstanceSerializer(children, many=True) 
        return serializer.data

class PageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the Sidebar list"""
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'status', 'layout', 'website']

class PageDetailSerializer(serializers.ModelSerializer):
    """Full serializer for the Editor Canvas metadata tab"""
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'status', 'layout', 'date', 'description', 'tags', 'website']

class SiteConfigSerializer(serializers.Serializer):
    """
    Custom serializer to aggregate Global Header, Footer, Block Definitions,
    and Layout Templates for the initial app load.
    """
    definitions = BlockDefinitionSerializer(many=True)
    layouts = LayoutTemplateSerializer(many=True)
    header = BlockInstanceSerializer(many=True)
    footer = BlockInstanceSerializer(many=True)
    websites = WebsiteSerializer(many=True)
    current_website = WebsiteSerializer()