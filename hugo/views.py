from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
import uuid 
from .models import Page, BlockDefinition, BlockInstance
from .serializers import (
    PageListSerializer, 
    PageDetailSerializer, 
    BlockDefinitionSerializer, 
    BlockInstanceSerializer,
    SiteConfigSerializer
)
from .importer import import_hugo_theme_structure

def editor_view(request):
    """Serves the Vue.js frontend application."""
    return render(request, 'hugo/index.html')

class CmsInitViewSet(viewsets.ViewSet):
    
    def list(self, request):
        definitions = BlockDefinition.objects.all()
        # Global blocks are defined by having parent=null, page=null
        header_blocks = BlockInstance.objects.filter(placement_key='header', page=None, parent=None).order_by('sort_order')
        footer_blocks = BlockInstance.objects.filter(placement_key='footer', page=None, parent=None).order_by('sort_order')
        
        data = {
            'definitions': definitions,
            'header': header_blocks,
            'footer': footer_blocks
        }
        serializer = SiteConfigSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def save_globals(self, request):
        """Saves header and footer blocks using the new relational structure."""
        
        # Helper to collect all UUIDs for deletion check
        incoming_ids = []
        def collect_ids(blocks):
            for block in blocks:
                incoming_ids.append(block['id'])
                if block.get('children'):
                    # The Vue frontend sends an array of column objects, each having a 'blocks' array
                    for col in block['children']:
                        if col.get('blocks'):
                            collect_ids(col['blocks'])
        
        collect_ids(request.data.get('header', []))
        collect_ids(request.data.get('footer', []))
        
        try:
            with transaction.atomic():
                # Delete old global blocks not present in the new payload
                BlockInstance.objects.filter(page=None, parent=None).exclude(id__in=incoming_ids).delete()
                
                # Save new/updated blocks recursively
                self._save_blocks_recursive(request.data.get('header', []), placement_key='header', page=None)
                self._save_blocks_recursive(request.data.get('footer', []), placement_key='footer', page=None)

            return Response({'status': 'saved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _save_blocks_recursive(self, blocks_data, placement_key, page, parent=None):
        """Helper to save a list of blocks and their children."""
        for index, block_data in enumerate(blocks_data):
            # Ensure ID exists for update_or_create; generate new if necessary
            block_id = block_data.get('id') or uuid.uuid4()
            
            block_instance, _ = BlockInstance.objects.update_or_create(
                id=block_id,
                defaults={
                    'definition_id': block_data['type'],
                    'page': page,
                    'parent': parent,
                    'placement_key': placement_key,
                    'sort_order': index,
                    'params': block_data.get('params', {})
                }
            )
            
            # --- Handle Children (Nesting) ---
            if block_data.get('children'):
                
                # Delete old children of this parent not present in the incoming payload
                incoming_child_ids = []
                for col in block_data['children']:
                     if col.get('blocks'):
                         for child in col['blocks']:
                             if 'id' in child: incoming_child_ids.append(child['id'])
                
                block_instance.children.exclude(id__in=incoming_child_ids).delete()

                for col_index, col_data in enumerate(block_data['children']):
                    # This handles the column structure sent by the Vue frontend
                    
                    if col_data.get('blocks'):
                        col_placement_key = f"col_{col_index}"
                        
                        # Recursively save blocks inside the column
                        self._save_blocks_recursive(
                            col_data['blocks'], 
                            placement_key=col_placement_key, 
                            page=None, # Nested blocks do not link to the page directly
                            parent=block_instance # Link to the 'flex_columns' parent instance
                        )

class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by('-updated_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PageListSerializer
        return PageDetailSerializer

    @action(detail=False, methods=['get'])
    def content(self, request, pk=None):
        """
        Returns the 'main' blocks for this specific page.
        """
        page = self.get_object()
        # Fetch only top-level blocks for the 'main' zone
        blocks = BlockInstance.objects.filter(page=page, placement_key='main', parent=None).order_by('sort_order')
        serializer = BlockInstanceSerializer(blocks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_content(self, request, pk=None):
        """
        Saves the page metadata and block content using the new relational structure.
        """
        page = self.get_object()
        top_level_blocks_data = request.data.get('blocks', [])
        
        # 1. Collect all UUIDs from the incoming payload (for deletion check)
        all_incoming_ids = []
        def collect_ids(blocks):
            for block in blocks:
                all_incoming_ids.append(block['id'])
                if block.get('children'):
                    # The Vue frontend sends an array of column objects, each having a 'blocks' array
                    for col in block['children']:
                        if col.get('blocks'):
                            collect_ids(col['blocks'])
        collect_ids(top_level_blocks_data)

        try:
            with transaction.atomic():
                # Delete existing blocks belonging to this page that are NOT in the payload
                page.main_blocks.exclude(id__in=all_incoming_ids).delete()
                
                # 2. Save top-level blocks and their children recursively
                self._save_blocks_recursive(
                    top_level_blocks_data, 
                    placement_key='main', 
                    page=page, 
                    parent=None
                )
            
            return Response({'status': 'saved', 'page_id': page.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    def _save_blocks_recursive(self, blocks_data, placement_key, page, parent=None):
        """Helper to save a list of blocks and their children. Same as CmsInitViewSet's helper."""
        for index, block_data in enumerate(blocks_data):
            block_id = block_data.get('id') or uuid.uuid4()
            
            block_instance, _ = BlockInstance.objects.update_or_create(
                id=block_id,
                defaults={
                    'definition_id': block_data['type'],
                    'page': page,
                    'parent': parent,
                    'placement_key': placement_key,
                    'sort_order': index,
                    'params': block_data.get('params', {})
                }
            )
            
            if block_data.get('children'):
                
                incoming_child_ids = []
                for col in block_data['children']:
                     if col.get('blocks'):
                         for child in col['blocks']:
                             if 'id' in child: incoming_child_ids.append(child['id'])
                
                block_instance.children.exclude(id__in=incoming_child_ids).delete()

                for col_index, col_data in enumerate(block_data['children']):
                    if col_data.get('blocks'):
                        col_placement_key = f"col_{col_index}"
                        
                        self._save_blocks_recursive(
                            col_data['blocks'], 
                            placement_key=col_placement_key, 
                            page=None, 
                            parent=block_instance
                        )

    @action(detail=False, methods=['post'])
    def import_theme(self, request):
        """
        Custom endpoint to trigger theme import logic.
        """
        theme_name = request.data.get('theme_name', 'default-mock')
        
        try:
            result = import_hugo_theme_structure(theme_name)
            return Response({'status': 'success', 'message': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)