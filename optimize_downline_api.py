import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

def main():
    api = Api.objects.filter(name="Get Downline List").first()
    if not api:
        print("API 'Get Downline List' not found.")
        return

    content = """
from ecommerce_app.models import Profile, Order, KYC
from django.db.models import Prefetch

if request.user.is_authenticated:
    try:
        user_id = request.data.get('user_id')
        if not user_id:
            user_id = request.user.id
            
        root_profile = Profile.objects.select_related('user').get(user__id=user_id)
        
        # 1. Fetch ALL relevant data into memory to prevent N+1 queries
        all_profiles = Profile.objects.select_related('user', 'user__kyc', 'sponsor', 'sponsor__user').all()
        
        # Build memory structures
        profile_dict = {p.id: p for p in all_profiles}
        children_map = {}
        for p in all_profiles:
            parent_id = p.parent_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(p)
            
        # Precompute latest paid order package name per user
        paid_orders = Order.objects.filter(status='paid').prefetch_related('items__product__category').order_by('-created_at')
        package_map = {}
        for order in paid_orders:
            uid = order.user_id
            if uid not in package_map:
                first_item = order.items.first()
                if first_item and first_item.product and first_item.product.category:
                    package_map[uid] = first_item.product.category.name
                else:
                    package_map[uid] = 'Unknown'
        
        def calculate_sponsor_level_mem(target_profile, root_id):
            level = 1
            current = target_profile
            
            while current.sponsor_id:
                if current.sponsor_id == root_id:
                    return level
                current = profile_dict.get(current.sponsor_id)
                if not current:
                    break
                level += 1
                if level > 100:
                    break
            return "Spillover"

        all_members = []
        
        def traverse_memory(current_profile, side_label):
            children = children_map.get(current_profile.id, [])
            for child in children:
                child_side = ""
                if current_profile.id == root_profile.id:
                    child_side = "Left" if child.position == 'L' else "Right"
                else:
                    child_side = side_label
                    
                sponsor_name = child.sponsor.user.first_name if child.sponsor else "N/A"
                sponsor_username = child.sponsor.user.username if child.sponsor else "N/A"
                
                package_name = package_map.get(child.user.id, "Inactive" if not child.is_active else "Unknown")
                
                kyc_status = "Not Submitted"
                try:
                    if hasattr(child.user, 'kyc'):
                        kyc_status = child.user.kyc.status
                except Exception:
                    pass
                
                level = calculate_sponsor_level_mem(child, root_profile.id)
                
                member_data = {
                    "user_id": child.user.id,
                    "name": child.user.first_name,
                    "username": child.user.username,
                    "side": child_side,
                    "sponsor_name": sponsor_name,
                    "sponsor_username": sponsor_username,
                    "package": package_name,
                    "kyc_status": kyc_status,
                    "is_active": child.is_active,
                    "level": level,
                    "join_date": child.created_at.strftime('%Y-%m-%d')
                }
                all_members.append(member_data)
                
                traverse_memory(child, child_side)

        # Start traversal
        traverse_memory(root_profile, "Unknown")
        
        response_data['status_code'] = 200
        response_data['data'] = all_members
        response_data['message'] = "Downline members fetched successfully (Optimized)"
        response_data['total_count'] = len(all_members)
        
    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""
    api.content = content
    api.version = float(api.version) + 0.1
    api.save()
    print(f"Successfully Optimized 'Get Downline List' API! New version: {api.version}")

if __name__ == '__main__':
    main()
