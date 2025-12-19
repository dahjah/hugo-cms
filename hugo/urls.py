from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, CmsInitViewSet, editor_view, WebsiteViewSet, 
    StorageSettingsViewSet, FileUploadViewSet, DeploymentProviderViewSet,
    TemplateCategoryViewSet, SiteTemplateViewSet, serve_preview_asset
)

router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
router.register(r'init', CmsInitViewSet, basename='cms-init')
router.register(r'websites', WebsiteViewSet, basename='website')
router.register(r'storage-settings', StorageSettingsViewSet, basename='storage-settings')
router.register(r'deployment-providers', DeploymentProviderViewSet, basename='deployment-provider')
router.register(r'files', FileUploadViewSet, basename='file-upload')
router.register(r'template-categories', TemplateCategoryViewSet, basename='template-category')
router.register(r'templates', SiteTemplateViewSet, basename='site-template')

urlpatterns = [
    path('', editor_view, name='editor'),  # Serve the Vue app at root
    path('site/<str:website_id>/', editor_view, name='editor-with-website'),  # With website ID
    path('api/sites/<uuid:website_id>/preview/', serve_preview_asset, {'path': ''}, name='serve-preview-root'),
    path('api/sites/<uuid:website_id>/preview/<path:path>', serve_preview_asset, name='serve-preview-asset'),
    path('api/', include(router.urls)),    # API endpoints
]