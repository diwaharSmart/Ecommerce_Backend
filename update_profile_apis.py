
import os
import django
import uuid
from django.db.models import Sum

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Updating Profile APIs...")

# 1. Update Get Profile API
get_profile_content = """
from ecommerce_app.models import Transaction, KYC
from django.db.models import Sum

if request.user.is_authenticated:
    try:
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
"""

# Try to find existing Get Profile Key
try:
    api = Api.objects.get(name="Get Profile")
    print(f"Updating 'Get Profile' (Key: {api.key})")
    api.content = get_profile_content
    api.save()
except Api.DoesNotExist:
    key_profile = str(uuid.uuid4())
    print(f"Creating 'Get Profile' (Key: {key_profile})")
    Api.objects.create(
        key=key_profile,
        name="Get Profile",
        method="POST",
        content=get_profile_content,
        version=1.1
    )


# 2. Create Edit Profile Picture API
edit_pic_content = """
from ecommerce_app.models import Profile
from django.core.files.storage import default_storage

if request.user.is_authenticated:
    profile_image = request.FILES.get('profile_image')
    
    if profile_image:
        try:
            profile = request.user.profile
            # If replacing, maybe delete old? Django ImageField handles replacement specifically if using same name, 
            # but usually it creates new unique name. 
            profile.profile_image = profile_image
            profile.save()
            
            image_url = request.build_absolute_uri(profile.profile_image.url)
            
            response_data['status_code'] = 200
            response_data['message'] = "Profile picture updated successfully"
            response_data['data'] = {"profile_image": image_url}
        except Exception as e:
            response_data['status_code'] = 500
            response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "No image file provided (key: profile_image)"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

# Check if exists (unlikely)
try:
    api = Api.objects.get(name="Edit Profile Picture")
    print(f"Updating 'Edit Profile Picture' (Key: {api.key})")
    api.content = edit_pic_content
    api.save()
except Api.DoesNotExist:
    key_edit_pic = str(uuid.uuid4())
    print(f"Creating 'Edit Profile Picture' (Key: {key_edit_pic})")
    Api.objects.create(
        key=key_edit_pic,
        name="Edit Profile Picture",
        method="POST",
        content=edit_pic_content,
        version=1.0
    )

print("Done.")
