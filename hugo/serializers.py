from rest_framework import serializers
from .models import Page, BlockDefinition, BlockInstance, LayoutTemplate, Website, UploadedFile, StorageSettings, SiteTemplate, TemplateCategory
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
        fields = ['id', 'label', 'icon', 'has_visual_preview', 'default_params', 'schema', 'is_container']

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


# --- Template Serializers ---

class TemplateCategorySerializer(serializers.ModelSerializer):
    """Serializer for template categories."""
    template_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateCategory
        fields = ['slug', 'name', 'description', 'order', 'template_count']
    
    def get_template_count(self, obj):
        return obj.templates.filter(is_public=True).count()


class SiteTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template gallery listing."""
    
    class Meta:
        model = SiteTemplate
        fields = ['id', 'slug', 'name', 'description', 'thumbnail_url', 'tags', 'is_featured', 'created_by']


class SiteTemplateDetailSerializer(serializers.ModelSerializer):
    """Full serializer for template detail and import."""
    
    class Meta:
        model = SiteTemplate
        fields = ['id', 'slug', 'name', 'description', 'thumbnail_url', 'tags', 
                  'base_css', 'pages_json', 'placeholder_schema', 'created_by', 
                  'is_featured', 'is_public', 'created_at', 'updated_at']


class CreateTemplateFromWebsiteSerializer(serializers.Serializer):
    """Serializer for creating a template from an existing website."""
    website_id = serializers.UUIDField()
    template_slug = serializers.SlugField(max_length=50)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    thumbnail_url = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')


class CreateWebsiteFromTemplateSerializer(serializers.Serializer):
    """Serializer for creating a new website from a template."""
    template_slug = serializers.SlugField(max_length=50)
    website_name = serializers.CharField(max_length=200)
    website_slug = serializers.CharField(max_length=200)