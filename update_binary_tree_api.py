
import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Updating Binary Tree API...")

binary_tree_content = """
from ecommerce_app.models import Profile, User, Order
from django.shortcuts import get_object_or_404

def get_node_data(profile, current_level, max_level):
    if not profile or current_level > max_level:
        return None
    
    # Logic to determing Package Name
    # Based on latest Paid Order -> First Product -> Category Name
    package_name = "None"
    if profile.is_active:
        # Optimziation: This might query DB for every node. 
        # For 3 levels (1 + 2 + 4 + 8 = 15 nodes), it's acceptable.
        latest_order = Order.objects.filter(user=profile.user, status='paid').order_by('-created_at').first()
        if latest_order:
            first_item = latest_order.items.first()
            if first_item and first_item.product and first_item.product.category:
                package_name = first_item.product.category.name
    
    data = {
        "user_id": profile.user.id,
        "username": profile.user.username,
        "first_name": profile.user.first_name, # Added for better UI
        "profile_image": request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
        "position": profile.position,
        "is_active": profile.is_active,
        "package_amount": float(profile.package_amount),
        "package_name": package_name, # <--- NEW FIELD
        "total_left_pv": profile.total_left_pv,
        "total_right_pv": profile.total_right_pv,
        "left": None,
        "right": None
    }
    
    # Find Left Child
    left_child = Profile.objects.filter(parent=profile.user.profile, position='L').first()
    if left_child:
        data["left"] = get_node_data(left_child, current_level + 1, max_level)
    
    # Find Right Child
    right_child = Profile.objects.filter(parent=profile.user.profile, position='R').first()
    if right_child:
        data["right"] = get_node_data(right_child, current_level + 1, max_level)
        
    return data

if request.user.is_authenticated:
    target_user_id = request.data.get('user_id')
    user = request.user
    
    if target_user_id:
        try:
             target_user = User.objects.get(id=target_user_id)
             # Visualization typically starts from the requested user or root
             user = target_user
        except User.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "User not found"
    
    if 'status_code' not in response_data or response_data['status_code'] == 200:
        try:
            root_profile = user.profile
            tree_data = get_node_data(root_profile, 0, 3) # level 0 + 3 levels down
            
            response_data['status_code'] = 200
            response_data['data'] = tree_data
            response_data['message'] = "Binary tree fetched successfully"
        except Exception as e:
            response_data['status_code'] = 500
            response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

# Update existing API
try:
    api = Api.objects.get(name="Get Binary Tree")
    print(f"Updating 'Get Binary Tree' (Key: {api.key})")
    api.content = binary_tree_content
    api.save()
except Api.DoesNotExist:
    print("Error: 'Get Binary Tree' API not found to update.")

print("Done.")
