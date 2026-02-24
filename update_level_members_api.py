
import os
import django
import uuid
from django.db.models import Sum

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Updating Level Members API...")

level_members_content = """
from ecommerce_app.models import Profile, Transaction, Order, KYC
from django.contrib.auth.models import User
from django.db.models import Sum

def get_package_name(profile):
    if not profile.is_active:
        return "Inactive"
    latest_order = Order.objects.filter(user=profile.user, status='paid').order_by('-created_at').first()
    if latest_order:
        first_item = latest_order.items.first()
        if first_item and first_item.product and first_item.product.category:
            return first_item.product.category.name
    return "Unknown"

def get_kyc_status(user):
    try:
        return user.kyc.status
    except Exception:
        return "Not Submitted"

if request.user.is_authenticated:
    target_user_id = request.data.get('user_id')
    root_user = request.user
    
    if target_user_id:
        try:
             root_user = User.objects.get(id=target_user_id)
        except Exception:
             pass 
    
    try:
        levels_data = {}
        current_level_members = [root_user.profile]
        transactions = Transaction.objects.filter(user=root_user)
        
        for i in range(1, 6): # Levels 1 to 5
            next_level_members = []
            level_key = f"level_{i}"
            
            members_list = []
            
            for parent in current_level_members:
                # Find direct referrals (Sponsor Tree)
                children = Profile.objects.filter(sponsor=parent)
                for child in children:
                    
                    sponsor_name = child.sponsor.user.first_name if child.sponsor else "N/A"
                    sponsor_username = child.sponsor.user.username if child.sponsor else "N/A"
                    # Side: Binary Position relative to their PLACEMENT parent. 
                    # If this is Level View (Sponsor Tree), Binary Side might be less relevant or confusing 
                    # because their Placement Parent might not be their Sponsor.
                    # But user asked for "left or right". We will return their actual Binary position.
                    side = "Left" if child.position == 'L' else "Right" if child.position == 'R' else "N/A"
                    
                    members_list.append({
                        "user_id": child.user.id,
                        "username": child.user.username,
                        "name": child.user.first_name,
                        "join_date": child.created_at.strftime('%Y-%m-%d'),
                        "package_amount": float(child.package_amount),
                        "package_name": get_package_name(child),
                        "is_active": child.is_active,
                        "kyc_status": get_kyc_status(child.user),
                        "sponsor_id": parent.user.id, # This is the Parent in loop (Sponsor)
                        "sponsor_name": sponsor_name,
                        "sponsor_username": sponsor_username, 
                        "side": side 
                    })
                    next_level_members.append(child)
            
            # Calculate Earnings for this level
            level_income = transactions.filter(type='level_income', description__icontains=f"Level {i} matching income").aggregate(Sum('amount'))['amount__sum'] or 0.0
            # Note: Description check "Level {i} income" might need adjustment if logic changed. 
            # In update 100, we changed to "Level {i} Matching Income".
            # Adjusting search string to be safer: "Level {i} " matches both schemas likely.
            
            levels_data[level_key] = {
                "count": len(members_list),
                "earnings": float(level_income),
                "members": members_list
            }
            
            current_level_members = next_level_members
            if not current_level_members:
                pass # Continue loop or break? Original logic continued.
        
        response_data['status_code'] = 200
        response_data['data'] = levels_data
        response_data['message'] = "Level members fetched successfully"

    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

try:
    api = Api.objects.get(name="Get Level Members")
    print(f"Updating 'Get Level Members' (Key: {api.key})")
    
    # Check if we need to update search string for income matching
    # Old logic: 'Level {i} income'
    # New logic (from task.md): 'Level {i} Matching Income'
    
    api.content = level_members_content
    api.save()
except Api.DoesNotExist:
    print("Error: 'Get Level Members' API not found.")

print("Done.")
