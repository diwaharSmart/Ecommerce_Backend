
import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Creating Downline List API...")

downline_content = """
from ecommerce_app.models import Profile, Order, KYC
from django.db.models import Q

def calculate_sponsor_level(target_profile, root_profile):
    level = 1
    current = target_profile
    if not current.sponsor:
        return "Spillover" # No sponsor (Root)
        
    # Traversing up the SPONSOR tree
    temp_sponsor = current.sponsor
    while temp_sponsor:
        if temp_sponsor == root_profile:
            return level
        temp_sponsor = temp_sponsor.sponsor
        level += 1
        if level > 100: # Safety break
            return "Spillover" # or distant
            
    return "Spillover" # Reached top without hitting root

def get_package_name(profile):
    if not profile.is_active:
        return "Inactive"
    # Logic: Latest Paid Order -> First Item -> Category Name
    latest_order = Order.objects.filter(user=profile.user, status='paid').order_by('-created_at').first()
    if latest_order:
        first_item = latest_order.items.first()
        if first_item and first_item.product and first_item.product.category:
            return first_item.product.category.name
    return "Unknown" # Active but no order found? (e.g. manual activation)

def get_kyc_status(user):
    try:
        return user.kyc.status
    except Exception:
        return "Not Submitted"

def traverse_binary_tree(current_profile, side_label, member_list, root_profile):
    # Find children in Binary Tree
    children = Profile.objects.filter(parent=current_profile)
    
    for child in children:
        # Determine strict binary side relative to the immediate parent
        # But user wants "Left or Right" relative to HIM (the Root).
        # We pass 'side_label' down. 
        # For the ROOT's immediate children, we set the label.
        # For descendants, they inherit the label of the branch.
        
        child_side = ""
        if current_profile == root_profile:
            # We are at root, set the main side
            child_side = "Left" if child.position == 'L' else "Right"
        else:
            # We are deep, inherit from parent call
            child_side = side_label
            
        # Collect Data
        sponsor_name = child.sponsor.user.first_name if child.sponsor else "N/A"
        sponsor_username = child.sponsor.user.username if child.sponsor else "N/A"
        
        level = calculate_sponsor_level(child, root_profile)
        
        member_data = {
            "user_id": child.user.id,
            "name": child.user.first_name,
            "username": child.user.username,
            "side": child_side, # Left or Right leg of Root
            "sponsor_name": sponsor_name,
            "sponsor_username": sponsor_username,
            "package": get_package_name(child),
            "kyc_status": get_kyc_status(child.user),
            "is_active": child.is_active,
            "level": level,
            "join_date": child.created_at.strftime('%Y-%m-%d')
        }
        member_list.append(member_data)
        
        # Recurse
        traverse_binary_tree(child, child_side, member_list, root_profile)


if request.user.is_authenticated:
    try:
        root_profile = request.user.profile
        all_members = []
        
        # Start traversal
        # We handle Left and Right branches explicitly from root to set initial label correct?
        # Or just generic recusion. 
        # Generic recursion works if we handle 'current_profile == root_profile' inside.
        
        traverse_binary_tree(root_profile, "Unknown", all_members, root_profile)
        
        response_data['status_code'] = 200
        response_data['data'] = all_members
        response_data['message'] = "Downline members fetched successfully"
        response_data['total_count'] = len(all_members)
        
    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_downline = str(uuid.uuid4())
Api.objects.create(
    key=key_downline,
    name="Get Downline List",
    method="POST",
    content=downline_content,
    version=1.0
)
print(f"Created 'Get Downline List' API: {key_downline}")
print("Done.")
