from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, CmsInitViewSet, editor_view, WebsiteViewSet, 
    StorageSettingsViewSet, FileUploadViewSet, DeploymentProviderViewSet,
    TemplateCategoryViewSet, SiteTemplateViewSet
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
    path('<str:website_id>/', editor_view, name='editor-with-website'),  # With website ID
    path('api/', include(router.urls)),    # API endpoints
]