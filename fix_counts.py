import os
import django
import sys

os.environ['USE_UAT_DB'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Profile

def fix_all_counts():
    print("Fetching all profiles...")
    profiles = list(Profile.objects.all().order_by('-id'))
    prof_dict = {p.id: p for p in profiles}
    
    print("Resetting and calculating full tree recursively...")
    # Clean slate
    for p in profiles:
        p._temp_left = 0
        p._temp_right = 0
        
    # Process bottom-up since list is ordered descending by ID
    # Actually standard while loop is safer
    for p in profiles:
        curr = p
        while curr.parent_id:
            parent = prof_dict.get(curr.parent_id)
            if not parent:
                break
                
            if curr.position == 'L':
                parent._temp_left += 1
            elif curr.position == 'R':
                parent._temp_right += 1
                
            curr = parent
            
    # Apply back
    print("Applying computed values to objects...")
    to_update = []
    for p in profiles:
        if getattr(p, '_temp_left', 0) != getattr(p, 'total_left_count', 0) or getattr(p, '_temp_right', 0) != getattr(p, 'total_right_count', 0):
            p.total_left_count = p._temp_left
            p.total_right_count = p._temp_right
            to_update.append(p)
            
    print(f"Updating {len(to_update)} profiles bulk...")
    Profile.objects.bulk_update(to_update, ['total_left_count', 'total_right_count'], batch_size=300)
    print("Done! Left/Right counts are fixed.")

if __name__ == '__main__':
    fix_all_counts()
