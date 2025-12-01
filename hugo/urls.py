from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, CmsInitViewSet, editor_view, WebsiteViewSet

router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
router.register(r'init', CmsInitViewSet, basename='cms-init')
router.register(r'websites', WebsiteViewSet, basename='website')

urlpatterns = [
    path('', editor_view, name='editor'),  # Serve the Vue app at root
    path('api/', include(router.urls)),    # API endpoints
]