from django.contrib import admin
from .models import Page, BlockDefinition, BlockInstance, LayoutTemplate, Website, SiteTemplate

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'theme_preset', 'created_at']
    search_fields = ['name', 'slug']
    list_editable = ['theme_preset']

@admin.register(SiteTemplate)
class SiteTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'theme_preset', 'is_featured']
    list_filter = ['is_featured', 'theme_preset']


@admin.register(LayoutTemplate)
class LayoutTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'label', 'get_zones', 'description']
    search_fields = ['id', 'label', 'description']
    ordering = ['label']
    
    def get_zones(self, obj):
        return ', '.join(obj.zones)
    get_zones.short_description = 'Zones'

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'layout', 'status', 'date', 'updated_at']
    list_filter = ['status', 'layout']
    search_fields = ['title', 'slug', 'description']
    ordering = ['-updated_at']

@admin.register(BlockDefinition)
class BlockDefinitionAdmin(admin.ModelAdmin):
    list_display = ['id', 'label', 'icon', 'has_visual_preview']
    search_fields = ['id', 'label']
    ordering = ['label']

@admin.register(BlockInstance)
class BlockInstanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'definition', 'placement_key', 'page', 'parent', 'sort_order']
    list_filter = ['placement_key', 'definition']
    search_fields = ['id']
    ordering = ['sort_order']

from .deployment_models import DeploymentProvider, DeploymentHistory

@admin.register(DeploymentProvider)
class DeploymentProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'enabled', 'is_default', 'created_at']
    list_filter = ['provider_type', 'enabled', 'is_default']
    search_fields = ['name', 'cf_account_id', 'pages_project_name']
    list_editable = ['enabled', 'is_default']

@admin.register(DeploymentHistory)
class DeploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['website', 'deployment_provider', 'status', 'started_at', 'hugo_version', 'build_duration_seconds']
    list_filter = ['status', 'deployment_provider', 'started_at']
    search_fields = ['website__name', 'error_message']
    readonly_fields = ['build_output', 'error_traceback']

