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
        wallet = request.user.wallet
        
        # 1. Sponsor Info
        sponsor_data = None
        if profile.sponsor:
            sponsor_data = {
                "id": profile.sponsor.user.id,
                "username": profile.sponsor.user.username,
                "name": profile.sponsor.user.first_name
            }
            
        # 2. Total Earnings
        # Sum of income types. 
        # Types seen so far: 'level_income', 'binary_income'. 
        # 'deposit' is usually payin (not earning). 'pin_credit' is transfer.
        # Let's sum 'level_income' and 'binary_income'.
        income_types = ['level_income', 'binary_income', 'referral_income', 'roi'] # Add others if any
        total_earnings = Transaction.objects.filter(
            user=request.user, 
            type__in=income_types, 
            direction='deposit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        # 3. Total Team Count
        # Profile has total_left_count and total_right_count updated by Register API logic
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
            "wallet_balance": float(wallet.current_balance),
            "sponsor": sponsor_data,
            "position": profile.position,
            "total_earnings": float(total_earnings),
            "total_team_count": total_team,
            "kyc_status": kyc_status,
            "package_amount": float(profile.package_amount),
            # Detailed PV stats if needed
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