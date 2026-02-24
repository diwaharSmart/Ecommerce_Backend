
import os
import django
import uuid
from decimal import Decimal
from django.db.models import Sum, Q  # Added Q here
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Updating MLM Dashboard API (V2)...")

dashboard_content = """
from ecommerce_app.models import Transaction, Order, Profile, Wallet
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

if request.user.is_authenticated:
    try:
        user = request.user
        profile = user.profile
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # --- 1. User & Sponsor Info ---
        sponsor_data = {
            "username": "N/A", 
            "first_name": "N/A"
        }
        if profile.sponsor:
            sponsor_data = {
                "username": profile.sponsor.user.username,
                "first_name": profile.sponsor.user.first_name
            }

        # --- 2. Income Stats ---
        # Sum of income credit transactions (Binary + Level + Referral + ROI + etc)
        # Assuming 'deposit' direction and relevant types.
        income_types = ['binary_income', 'level_income', 'referral_bonus'] # Add others if needed
        total_income_credit = Transaction.objects.filter(
            user=user, 
            direction='deposit', 
            type__in=income_types
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        sum_binary_income = Transaction.objects.filter(
            user=user, type='binary_income'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        sum_level_income = Transaction.objects.filter(
            user=user, type='level_income'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        count_binary_pairs = Transaction.objects.filter(
            user=user, type='binary_income'
        ).count()

        # --- 3. Team Stats ---
        total_binary_tree_count = profile.total_left_count + profile.total_right_count
        
        # Level Team Count (Sponsor Tree - 5 Levels)
        # We need to traverse down to count. 
        # For efficiency, we can cache or just do simplified traversal (since max level is usually small for dashboard view or limited).
        # We will do a quick traversal for 5 levels (common requirement).
        level_team_count = 0
        current_level_members = [profile]
        for i in range(1, 6): # 5 Levels
            next_level_members = []
            if not current_level_members:
                break
            # Find children of current members
            children = Profile.objects.filter(sponsor__in=current_level_members)
            count = children.count()
            level_team_count += count
            next_level_members = list(children) # Queryset to list for next iter
            current_level_members = next_level_members

        sum_topup_wallet = float(wallet.top_up_balance)


        # --- 4. Binary Income Overview (PV) ---
        # "Today Left pv Right pv"
        # Note: Models do NOT track daily PV history efficiently. 
        # We serve "All Time" (Total) and "Current" (Carry Forward).
        # For "Today" and "Week", we return 0.0 or placeholders as calculating it requires complex order tree traversal.
        
        # All Time
        all_time_left = profile.total_left_pv
        all_time_right = profile.total_right_pv
        
        # Current (Live/Unmatched)
        current_left = profile.current_left_pv
        current_right = profile.current_right_pv
        
        # Today/Week Placeholder (Requires 'PVLog' model for accuracy)
        today_left = 0
        today_right = 0
        week_left = 0
        week_right = 0
        
        
        # --- 5. Level Income Overview (1-5) ---
        level_overview = []
        today = timezone.now().date()
        
        for i in range(1, 6):
            # Description text based matching: "Level {i} Matching Income"
            # We match partial string "Level 1" etc.
            # Warning: "Level 10" contains "Level 1". 
            # Use regex or precise formatting if possible. 
            # Current format: "Level {i} Matching Income..."
            # Querying 'Level {i} ' ensures distinction if i < 10.
            
            search_str = f"Level {i} " 
            
            # All Time
            total = Transaction.objects.filter(
                user=user, 
                type='level_income', 
                description__startswith=search_str
            ).aggregate(Sum('amount'))['amount__sum'] or 0.00
            
            # Today
            todays = Transaction.objects.filter(
                user=user, 
                type='level_income', 
                description__startswith=search_str,
                created_at__date=today
            ).aggregate(Sum('amount'))['amount__sum'] or 0.00
            
            level_overview.append({
                "level": i,
                "today_income": float(todays),
                "all_time_income": float(total)
            })

        # --- 6. Total Left/Right Counts ---
        total_left_count_tree = profile.total_left_count
        total_right_count_tree = profile.total_right_count
        
        # --- 7. Recent Orders ---
        orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
        orders_data = []
        for o in orders:
            orders_data.append({
                "id": o.id,
                "amount": float(o.total_amount),
                "pv": o.total_pv,
                "status": o.status,
                "date": o.created_at.strftime('%Y-%m-%d')
            })

        # --- Construct Response ---
        data = {
            "user_info": {
                "profile_pic": request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
                "username": user.username,
                "first_name": user.first_name,
            },
            "sponsor_info": sponsor_data,
            "overall_income": {
                "total_credit": float(total_income_credit),
                "binary_income_sum": float(sum_binary_income),
                "level_income_sum": float(sum_level_income),
                "binary_pair_matches": count_binary_pairs
            },
            "team_stats": {
                "total_binary_tree_count": total_binary_tree_count,
                "level_team_count": level_team_count,
                "topup_wallet_balance": sum_topup_wallet,
                "total_left_count": total_left_count_tree,
                "total_right_count": total_right_count_tree
            },
            "binary_pv_overview": {
                "today": {"left": today_left, "right": today_right},
                "this_week": {"left": week_left, "right": week_right},
                "all_time": {"left": all_time_left, "right": all_time_right},
                "current_carry_forward": {"left": current_left, "right": current_right}
            },
            "level_income_overview": level_overview,
            "recent_orders": orders_data
        }

        response_data['status_code'] = 200
        response_data['data'] = data
        response_data['message'] = "Dashboard data fetched successfully"

    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

try:
    api = Api.objects.get(name="Get MLM Dashboard")
    print(f"Updating 'Get MLM Dashboard' (Key: {api.key})")
    
    # Update content
    api.content = dashboard_content
    api.version = float(api.version) + 0.1
    api.save()
    
except Api.DoesNotExist:
    key_dash = str(uuid.uuid4())
    print(f"Creating 'Get MLM Dashboard' (Key: {key_dash})")
    Api.objects.create(
        key=key_dash,
        name="Get MLM Dashboard",
        method="POST",
        content=dashboard_content,
        version=1.1
    )

print("Done.")
