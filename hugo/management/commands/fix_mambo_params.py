from hugo.models import BlockInstance
from django.db import transaction

def fix_bad_params():
    print("Checking for blocks with malformed parameters...")
    blocks = BlockInstance.objects.filter(definition_id='cta_hero')
    fixed_count = 0
    
    with transaction.atomic():
        for block in blocks:
            params = block.params
            if '  background_image' in params:
                print(f"Fixing block {block.id}...")
                # Move value to correct key
                params['background_image'] = params.pop('  background_image')
                block.params = params
                block.save()
                fixed_count += 1
                
    print(f"Fixed {fixed_count} blocks.")

if __name__ == '__main__':
    fix_bad_params()
