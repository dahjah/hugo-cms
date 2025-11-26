from rest_framework import serializers
from .models import Page, BlockDefinition, BlockInstance

class BlockDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockDefinition
        fields = ['id', 'label', 'icon', 'has_visual_preview', 'default_params']

class BlockInstanceSerializer(serializers.ModelSerializer):
    # Flatten the type ID for the frontend (frontend expects 'type': 'hero', not nested object)
    type = serializers.ReadOnlyField(source='definition.id')
    
    class Meta:
        model = BlockInstance
        fields = ['id', 'type', 'params', 'zone', 'sort_order']

class PageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the Sidebar list"""
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'status', 'layout']

class PageDetailSerializer(serializers.ModelSerializer):
    """Full serializer for the Editor Canvas metadata tab"""
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'status', 'layout', 'date', 'description', 'tags']

class SiteConfigSerializer(serializers.Serializer):
    """
    Custom serializer to aggregate Global Header, Footer, and Block Definitions
    for the initial app load.
    """
    definitions = BlockDefinitionSerializer(many=True)
    header = BlockInstanceSerializer(many=True)
    footer = BlockInstanceSerializer(many=True)