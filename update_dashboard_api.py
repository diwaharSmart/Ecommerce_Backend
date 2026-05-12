import os
import sys
import django

sys.path.append("d:\\Ecommerce_Backend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

def update_dashboard_api():
    try:
        api = Api.objects.get(id=219)
        
        # New code for API 219
        new_content = """from ecommerce_app.models import Transaction, Order, Profile, Wallet, User
from ecommerce_app.serializers import TransactionSerializer
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

if request.user.is_authenticated:
    try:
        try:
            user = User.objects.get(username=request.data["username"])
        except:
            user = request.user
        
        profile = user.profile
        wallet, _ = Wallet.objects.get_or_create(user=user)

        # --- 1. User & Sponsor Info ---
        sponsor_data = {"username": "N/A", "first_name": "N/A"}
        if profile.sponsor:
            sponsor_data = {
                "username": profile.sponsor.user.username,
                "first_name": profile.sponsor.user.first_name
            }

        # --- 2. Income Stats & Weekly Balance ---
        # Current week logic (Starting Monday)
        today = timezone.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        weekly_binary = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit', 
            created_at__gte=start_of_week
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        weekly_level = Transaction.objects.filter(
            user=user, type='level_income', direction='credit', 
            created_at__gte=start_of_week
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        current_balance = float(weekly_binary) + float(weekly_level)

        # All-time Income
        sum_binary_income = Transaction.objects.filter(user=user, type='binary_income').aggregate(Sum('amount'))['amount__sum'] or 0.00
        sum_level_income = Transaction.objects.filter(user=user, type='level_income').aggregate(Sum('amount'))['amount__sum'] or 0.00
        total_income_credit = float(sum_binary_income) + float(sum_level_income)

        # --- 3. Transaction History ---
        all_txns = Transaction.objects.filter(user=user).order_by('-created_at')
        transactions_data = TransactionSerializer(all_txns, many=True).data

        # --- 4. Team Stats ---
        total_binary_tree_count = profile.total_left_count + profile.total_right_count
        
        # Level Team Count (5 Levels)
        level_team_count = 0
        current_level_members = [profile]
        for i in range(1, 6):
            if not current_level_members: break
            children = Profile.objects.filter(sponsor__in=current_level_members)
            level_team_count += children.count()
            current_level_members = list(children)

        # --- 5. Response Construction ---
        data = {
            "user_info": {
                "profile_pic": request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None,
                "username": user.username,
                "first_name": user.first_name,
            },
            "sponsor_info": sponsor_data,
            "wallet": {
                "current_balance": current_balance,
                "topup_balance": float(wallet.top_up_balance)
            },
            "overall_income": {
                "total_credit": float(total_income_credit),
                "binary_income_sum": float(sum_binary_income),
                "level_income_sum": float(sum_level_income),
                "weekly_balance": current_balance
            },
            "team_stats": {
                "total_binary_tree_count": total_binary_tree_count,
                "level_team_count": level_team_count,
                "total_left_count": profile.total_left_count,
                "total_right_count": profile.total_right_count
            },
            "binary_pv_overview": {
                "all_time": {"left": profile.total_left_pv, "right": profile.total_right_pv},
                "current_carry_forward": {"left": profile.current_left_pv, "right": profile.current_right_pv}
            },
            "transactions": transactions_data,
            "recent_orders": [] # Simplified for now
        }

        response_data['status_code'] = 200
        response_data['data'] = data
        response_data['message'] = "Dashboard data fetched successfully"

    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized\"""
        
        api.content = new_content
        api.save()
        print("API 219 updated successfully.")
        
    except Api.DoesNotExist:
        print("API 219 not found.")

if __name__ == '__main__':
    update_dashboard_api()
