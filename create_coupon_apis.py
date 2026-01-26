import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

# 20. Get Coupons API
get_coupons_content = """
from ecommerce_app.models import Coupon
from ecommerce_app.serializers import CouponSerializer
from django.utils import timezone

if request.user.is_authenticated:
    try:
        # Fetch active and non-expired coupons or all?
        # Usually users want to see all, but let's prioritize valid ones.
        # Let's return all for history, frontend can filter.
        coupons = Coupon.objects.filter(user=request.user).order_by('-created_at')
        serializer = CouponSerializer(coupons, many=True)
        
        response_data['status_code'] = 200
        response_data['message'] = "Coupons fetched successfully"
        response_data['data'] = serializer.data
        
    except Exception as e:
         response_data['status_code'] = 500
         response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_get_coupons = str(uuid.uuid4())
Api.objects.create(
    key=key_get_coupons,
    name="Get Coupons",
    method="POST",
    content=get_coupons_content,
    version=1.0
)
print(f"Created 'Get Coupons' with Key: {key_get_coupons}")


# 21. Redeem Coupon API
redeem_coupon_content = """
from ecommerce_app.models import Coupon, Wallet, Transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

if request.user.is_authenticated:
    coupon_id = request.data.get('coupon_id')
    
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, user=request.user)
            
            if not coupon.is_active:
                response_data['status_code'] = 400
                response_data['message'] = "Coupon is already used or inactive"
            elif coupon.valid_until and coupon.valid_until < timezone.now().date():
                response_data['status_code'] = 400
                response_data['message'] = "Coupon has expired"
            else:
                # Process Redemption
                amount = coupon.amount
                
                # Credit Wallet
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                wallet.current_balance += amount
                wallet.save()
                
                # Mark Used
                coupon.is_active = False
                coupon.save()
                
                # Transaction
                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    direction='credit',
                    type='deposit', # Using 'deposit' as generic credit, typically 'coupon' type better if supported
                    description=f"Redeemed Coupon #{coupon.id}"
                )
                
                response_data['status_code'] = 200
                response_data['message'] = f"Coupon redeemed! {amount} added to wallet."
                
        except Coupon.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "Coupon not found"
        except Exception as e:
             response_data['status_code'] = 500
             response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Coupon ID required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_redeem_coupon = str(uuid.uuid4())
Api.objects.create(
    key=key_redeem_coupon,
    name="Redeem Coupon",
    method="POST",
    content=redeem_coupon_content,
    version=1.0
)
print(f"Created 'Redeem Coupon' with Key: {key_redeem_coupon}")
