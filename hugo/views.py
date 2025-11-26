from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Page, BlockDefinition, BlockInstance
from .serializers import (
    PageListSerializer, 
    PageDetailSerializer, 
    BlockDefinitionSerializer, 
    BlockInstanceSerializer,
    SiteConfigSerializer
)

def editor_view(request):
    """Serves the Vue.js frontend application."""
    return render(request, 'hugo/index.html')

class CmsInitViewSet(viewsets.ViewSet):
    # ... (Same as before)
    def list(self, request):
        definitions = BlockDefinition.objects.all()
        header_blocks = BlockInstance.objects.filter(zone='header').order_by('sort_order')
        footer_blocks = BlockInstance.objects.filter(zone='footer').order_by('sort_order')
        
        data = {
            'definitions': definitions,
            'header': header_blocks,
            'footer': footer_blocks
        }
        serializer = SiteConfigSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def save_globals(self, request):
        return self._update_zone(request.data)

    def _update_zone(self, data):
        try:
            with transaction.atomic():
                for zone in ['header', 'footer']:
                    if zone in data:
                        BlockInstance.objects.filter(zone=zone, page=None).delete()
                        for index, block_data in enumerate(data[zone]):
                            BlockInstance.objects.create(
                                id=block_data.get('id'),
                                definition_id=block_data['type'],
                                page=None,
                                zone=zone,
                                sort_order=index,
                                params=block_data['params']
                            )
            return Response({'status': 'saved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PageViewSet(viewsets.ModelViewSet):
    # ... (Same as before)
    queryset = Page.objects.all().order_by('-updated_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PageListSerializer
        return PageDetailSerializer

    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        page = self.get_object()
        blocks = page.blocks.filter(zone='main').order_by('sort_order')
        serializer = BlockInstanceSerializer(blocks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_content(self, request, pk=None):
        page = self.get_object()
        blocks_data = request.data
        
        try:
            with transaction.atomic():
                incoming_ids = [b.get('id') for b in blocks_data if b.get('id')]
                page.blocks.filter(zone='main').exclude(id__in=incoming_ids).delete()

                for index, block_data in enumerate(blocks_data):
                    BlockInstance.objects.update_or_create(
                        id=block_data.get('id'),
                        defaults={
                            'page': page,
                            'zone': 'main',
                            'definition_id': block_data['type'],
                            'sort_order': index,
                            'params': block_data['params']
                        }
                    )
            return Response({'status': 'saved', 'page_id': page.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)