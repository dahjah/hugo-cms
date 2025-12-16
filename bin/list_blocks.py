
import os
import django
import sys
import json

sys.path.append('/home/djg/practice/hugo_cms/hugo_cms_gemini2/hugo_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hugo.models import BlockDefinition

def list_blocks():
    blocks = BlockDefinition.objects.all().order_by('id')
    available_blocks = []
    
    for block in blocks:
        block_info = {
            "id": block.id,
            "label": block.label,
            "description": block.schema.get('description', ''), # Assuming schema might have description at top level
            "is_container": block.is_container,
            "params": block.schema,
            "default_params": block.default_params 
        }
        available_blocks.append(block_info)

    print(json.dumps(available_blocks, indent=2))

if __name__ == "__main__":
    list_blocks()
