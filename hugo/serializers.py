from rest_framework import serializers
from .models import Page, BlockDefinition, BlockInstance, LayoutTemplate, Website, UploadedFile, StorageSettings
from .deployment_models import DeploymentProvider

class DeploymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentProvider
        fields = ['id', 'name', 'enabled', 'provider_type', 'cf_account_id', 'cf_zone_id', 'cf_r2_access_key', 'cf_r2_secret_key', 'cf_api_token', 'cf_bucket_name', 'custom_domain']
        extra_kwargs = {
            'cf_r2_secret_key': {'write_only': True},
            'cf_api_token': {'write_only': True}
        }

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'filename', 'file_url', 'file_size', 'content_type', 'uploaded_at']

class StorageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageSettings
        fields = ['id', 'storage_type', 's3_bucket', 's3_endpoint', 's3_access_key', 's3_secret_key', 's3_region', 's3_public_url', 'local_media_path', 'local_public_url']
        extra_kwargs = {
            's3_secret_key': {'write_only': True}
        }

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'name', 'slug', 'custom_css', 'deployment_provider']

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
        fields = ['id', 'title', 'slug', 'status', 'layout', 'website', 'last_published_at', 'updated_at']

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