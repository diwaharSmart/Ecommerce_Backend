import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

# --- Update Get Profile API ---
profile_api_code = """
from ecommerce_app.models import Transaction, KYC
from django.db.models import Sum
from django.contrib.auth import get_user_model

User = get_user_model()
if request.user.is_authenticated:
    try:
        username = request.data.get("username",None)
        if username:
            request.user= User.objects.get(username=username)
    
        profile = request.user.profile
        
        # 1. Sponsor Info
        sponsor_data = None
        if profile.sponsor:
            sponsor_data = {
                "id": profile.sponsor.user.id,
                "username": profile.sponsor.user.username,
                "name": profile.sponsor.user.first_name
            }
            
        # 2. Total Earnings
        income_types = ['level_income', 'binary_income', 'referral_income', 'roi']
        total_earnings = Transaction.objects.filter(
            user=request.user, 
            type__in=income_types, 
            direction='credit'  # Note: should be credit, but let's check what was used. The original had 'deposit'. I'll stick to 'credit'.
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        # Calculate new wallet balance (Total Binary + Total Level)
        binary_income_total = Transaction.objects.filter(
            user=request.user, type='binary_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        level_income_total = Transaction.objects.filter(
            user=request.user, type='level_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        new_wallet_balance = binary_income_total + level_income_total
        
        # 3. Total Team Count
        total_team = profile.total_left_count + profile.total_right_count
        
        # 4. KYC Status
        kyc_status = "Not Submitted"
        try:
            kyc = KYC.objects.get(user=request.user)
            kyc_status = kyc.status
        except KYC.DoesNotExist:
            pass
            
        data = {
            "username": request.user.username,
            "first_name": request.user.first_name,
            "email": request.user.email,
            "is_active": profile.is_active,
            "profile_image": request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
            "wallet_balance": float(new_wallet_balance),
            "sponsor": sponsor_data,
            "position": profile.position,
            "total_earnings": float(total_earnings),
            "total_team_count": total_team,
            "kyc_status": kyc_status,
            "package_amount": float(profile.package_amount),
            "total_left_pv": profile.total_left_pv,
            "total_right_pv": profile.total_right_pv,
            "current_left_pv": profile.current_left_pv,
            "current_right_pv": profile.current_right_pv,
        }
        
        response_data['status_code'] = 200
        response_data['data'] = data
        response_data['message'] = "Profile details fetched successfully"
        
    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

# --- Update Get MLM Dashboard API ---
dashboard_api_code = """
from ecommerce_app.models import Transaction, Order, Profile, Wallet, User
from django.db.models import Sum, Q
from django.utils import timezone
import datetime

if request.user.is_authenticated:
    try:
        try:
            user = User.objects.get(username=request.data["username"])
        except:
            user = request.user
        profile = user.profile
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # --- Date Setup ---
        today = timezone.now()
        start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

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
        income_types = ['binary_income', 'level_income', 'referral_bonus']
        total_income_credit = Transaction.objects.filter(
            user=user, 
            direction='credit', 
            type__in=income_types
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        sum_binary_income = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        sum_level_income = Transaction.objects.filter(
            user=user, type='level_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        count_binary_pairs = Transaction.objects.filter(
            user=user, type='binary_income'
        ).count()

        # --- 3. Team Stats ---
        total_binary_tree_count = profile.total_left_count + profile.total_right_count
        
        level_team_count = 0
        current_level_members = [profile]
        for i in range(1, 6):
            if not current_level_members:
                break
            children = Profile.objects.filter(sponsor__in=current_level_members)
            count = children.count()
            level_team_count += count
            current_level_members = list(children)

        sum_topup_wallet = float(wallet.top_up_balance)

        # --- 4. Binary/Level Daily & Weekly Overview ---
        # Today
        today_binary = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit', created_at__gte=start_of_today
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        today_level = Transaction.objects.filter(
            user=user, type='level_income', direction='credit', created_at__gte=start_of_today
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        today_total = today_binary + today_level

        # This Week
        weekly_binary = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit', created_at__gte=start_of_week
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        weekly_level = Transaction.objects.filter(
            user=user, type='level_income', direction='credit', created_at__gte=start_of_week
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        weekly_total = weekly_binary + weekly_level

        # --- 5. PV Overview (Placeholder for now) ---
        all_time_left = profile.total_left_pv
        all_time_right = profile.total_right_pv
        current_left = profile.current_left_pv
        current_right = profile.current_right_pv
        
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
            "daily_income": {
                "binary_income": float(today_binary),
                "level_income": float(today_level),
                "total_income": float(today_total)
            },
            "weekly_income": {
                "binary_income": float(weekly_binary),
                "level_income": float(weekly_level),
                "total_income": float(weekly_total)
            },
            "team_stats": {
                "total_binary_tree_count": total_binary_tree_count,
                "level_team_count": level_team_count,
                "topup_wallet_balance": sum_topup_wallet,
                "total_left_count": total_left_count_tree,
                "total_right_count": total_right_count_tree
            },
            "binary_pv_overview": {
                "all_time": {"left": all_time_left, "right": all_time_right},
                "current_carry_forward": {"left": current_left, "right": current_right}
            },
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
    p_api = Api.objects.get(name="Get Profile")
    p_api.content = profile_api_code.strip()
    p_api.version = float(p_api.version) + 0.1
    p_api.save()
    print("Updated Get Profile API")
except Api.DoesNotExist:
    pass

try:
    d_api = Api.objects.get(name="Get MLM Dashboard")
    d_api.content = dashboard_api_code.strip()
    d_api.version = float(d_api.version) + 0.1
    d_api.save()
    print("Updated Get MLM Dashboard API")
except Api.DoesNotExist:
    pass
