import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

key_dashboard = "91b1f76e-f709-499f-9e78-831ec42581e5"

dashboard_content = """
from ecommerce_app.models import Profile, Transaction, Order
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

if request.user.is_authenticated:
    target_username = request.data.get('username')
    user = request.user
    
    if target_username:
        try:
             user = User.objects.get(username=target_username)
        except Exception:
             # Fallback to self or error? User requested "pass username"
             # If not found, create error or default to self? 
             # Let's return error if specific username requested but not found.
             response_data['status_code'] = 404
             response_data['message'] = "User not found"
             # We need to stop further execution here.
             # In this exec() context, 'user' variable is used below.
             # We can't easy 'return', so we wrap logic in else or use flag.
             user = None 

    if user:
        try:
            profile = user.profile
            sponsor = profile.sponsor
            
            # --- 1. Basic Counts ---
            left_count = profile.total_left_count
            right_count = profile.total_right_count
            
            # --- 2. Pair Match Count ---
            transactions = Transaction.objects.filter(user=user)
            # Calculate total pairs by inspecting the amount (500 Rs = 1 pair)
            binary_income_total = transactions.filter(type='binary_income').aggregate(Sum('amount'))['amount__sum'] or 0.0
            pair_match_count = int(float(binary_income_total) / 500.0)
            
            # --- 3. Active Directs ---
            active_directs = Profile.objects.filter(sponsor=profile, is_active=True).count()
            total_directs = Profile.objects.filter(sponsor=profile).count()
            
            # --- 4. Level Stats (1-5) ---
            level_stats = []
            
            # ... (Existing Level Logic omitted for brevity? No, must include full content)
            # Re-implementing existing logic + enhancements
            
            current_level_members = [profile]
            for i in range(1, 6):
                next_level_members = []
                count = 0
                for parent in current_level_members:
                    children = Profile.objects.filter(sponsor=parent)
                    count += children.count()
                    next_level_members.extend(children)
                current_level_members = next_level_members
                
                # Earnings (Now 'Matching Level Income' based on new logic, but type is still 'level_income')
                # We filter by description or type.
                level_income = transactions.filter(type='level_income', description__icontains=f"Level {i}").aggregate(Sum('amount'))['amount__sum'] or 0.0
                
                level_stats.append({
                    "level": i,
                    "member_count": count,
                    "earnings": float(level_income)
                })

            # --- 5. Sales Report (PV) ---
            # Helper to get downline users for a leg
            def get_downline_users(root_profile):
                users = []
                # Recursive traversal or reuse 'total_left_count' logic? 
                # We need actual User objects to query Orders.
                # Breadth-first search
                queue = [root_profile]
                while queue:
                    node = queue.pop(0)
                    children = Profile.objects.filter(parent=node)
                    for child in children:
                        users.append(child.user)
                        queue.append(child)
                return users

            # Get Left and Right Leg Roots
            left_child = Profile.objects.filter(parent=profile, position='L').first()
            right_child = Profile.objects.filter(parent=profile, position='R').first()
            
            left_users = get_downline_users(left_child) if left_child else []
            if left_child: left_users.append(left_child.user) # Include the immediate child too
            
            right_users = get_downline_users(right_child) if right_child else []
            if right_child: right_users.append(right_child.user)

            # Date Ranges
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday()) # Monday
            
            # Query Orders
            def get_pv_sum(users, date_filter=None):
                clean_users = [u for u in users if u]
                if not clean_users: return 0
                qs = Order.objects.filter(user__in=clean_users, status='paid')
                if date_filter == 'today':
                    qs = qs.filter(created_at__date=today)
                elif date_filter == 'week':
                    qs = qs.filter(created_at__date__gte=start_of_week)
                return qs.aggregate(Sum('total_pv'))['total_pv__sum'] or 0

            sales_report = {
                "today": {
                    "left_pv": get_pv_sum(left_users, 'today'),
                    "right_pv": get_pv_sum(right_users, 'today')
                },
                "weekly": {
                    "left_pv": get_pv_sum(left_users, 'week'),
                    "right_pv": get_pv_sum(right_users, 'week')
                },
                "total": {
                    "left_pv": profile.total_left_pv,
                    "right_pv": profile.total_right_pv
                }
            }

            # --- 6. Sponsor Info ---
            sponsor_data = None
            if sponsor:
                sponsor_data = {
                    "id": sponsor.user.id,
                    "name": sponsor.user.first_name, # or user.name if extended
                    "username": sponsor.user.username
                }

            response_data['status_code'] = 200
            response_data['message'] = "Dashboard data fetched"
            response_data['data'] = {
                 "user_info": { "username": user.username, "name": user.first_name },
                 "sponsor_info": sponsor_data,
                 "left_count": left_count,
                 "right_count": right_count,
                 "pair_match_count": pair_match_count,
                 "active_directs": active_directs,
                 "total_directs": total_directs,
                 "level_stats": level_stats,
                 "sales_report": sales_report,
                 "business_stats": { # Keeping old structure too for backward compat if needed
                    "total_left_pv": profile.total_left_pv,
                    "total_right_pv": profile.total_right_pv,
                    "current_left_pv": profile.current_left_pv,
                    "current_right_pv": profile.current_right_pv,
                 }
            }

        except Exception as e:
            response_data['status_code'] = 500
            response_data['message'] = str(e)
            import traceback
            # Optional: response_data['trace'] = traceback.format_exc()
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

try:
    api = Api.objects.get(key=key_dashboard)
    api.content = dashboard_content
    api.save()
    print(f"Successfully updated Dashboard API (Key: {key_dashboard})")
except Api.DoesNotExist:
    print(f"Error: API with key {key_dashboard} not found. Trying to find by name...")
    try:
         api = Api.objects.get(name="Get MLM Dashboard")
         api.key = key_dashboard
         api.content = dashboard_content
         api.save()
         print(f"Successfully updated Dashboard API by Name and restored Key: {key_dashboard}")
    except Api.DoesNotExist:
         print("Error: API 'Get MLM Dashboard' not found.")
