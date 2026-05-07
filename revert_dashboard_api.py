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
             response_data['status_code'] = 404
             response_data['message'] = "User not found"
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
            # Revert to old count method or keep the fixed math logic? 
            # I will use the fixed math logic so pair counts are correct, as it's safe.
            binary_income_total = transactions.filter(type='binary_income').aggregate(Sum('amount'))['amount__sum'] or 0.0
            pair_match_count = int(float(binary_income_total) / 500.0)
            
            # --- 3. Active Directs ---
            active_directs = Profile.objects.filter(sponsor=profile, is_active=True).count()
            total_directs = Profile.objects.filter(sponsor=profile).count()
            
            # --- 4. Level Stats (1-5) ---
            level_stats = []
            
            current_level_members = [profile]
            for i in range(1, 6):
                next_level_members = []
                count = 0
                for parent in current_level_members:
                    children = Profile.objects.filter(sponsor=parent)
                    count += children.count()
                    next_level_members.extend(children)
                current_level_members = next_level_members
                
                level_income = transactions.filter(type='level_income', description__icontains=f"Level {i}").aggregate(Sum('amount'))['amount__sum'] or 0.0
                
                level_stats.append({
                    "level": i,
                    "member_count": count,
                    "earnings": float(level_income)
                })

            # --- 5. Sales Report (PV) ---
            def get_downline_users(root_profile):
                users = []
                queue = [root_profile]
                while queue:
                    node = queue.pop(0)
                    children = Profile.objects.filter(parent=node)
                    for child in children:
                        users.append(child.user)
                        queue.append(child)
                return users

            left_child = Profile.objects.filter(parent=profile, position='L').first()
            right_child = Profile.objects.filter(parent=profile, position='R').first()
            
            left_users = get_downline_users(left_child) if left_child else []
            if left_child: left_users.append(left_child.user)
            
            right_users = get_downline_users(right_child) if right_child else []
            if right_child: right_users.append(right_child.user)

            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            
            def get_pv_sum(users, date_filter=None):
                clean_users = [u for u in users if u]
                if not clean_users: return 0
                qs = Order.objects.filter(user__in=clean_users, status='paid')
                if date_filter == 'today':
                    qs = qs.filter(created_at__date=today)
                elif date_filter == 'week':
                    qs = qs.filter(created_at__date__gte=start_of_week)
                return float(qs.aggregate(Sum('total_pv'))['total_pv__sum'] or 0.0)

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
                    "name": sponsor.user.first_name,
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
                 "business_stats": {
                    "total_left_pv": profile.total_left_pv,
                    "total_right_pv": profile.total_right_pv,
                    "current_left_pv": profile.current_left_pv,
                    "current_right_pv": profile.current_right_pv,
                 }
            }

        except Exception as e:
            response_data['status_code'] = 500
            response_data['message'] = str(e)
            
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

try:
    api = Api.objects.get(key=key_dashboard)
    api.content = dashboard_content
    api.save()
    print(f"Successfully reverted Dashboard API (Key: {key_dashboard})")
except Api.DoesNotExist:
    pass
