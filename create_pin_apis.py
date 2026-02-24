
import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Creating Pin System Dynamic APIs...")

# 1. Request Pins API
request_pins_content = """
from ecommerce_app.models import PinRequest

if request.user.is_authenticated:
    number_of_pins = request.data.get('number_of_pins')
    
    if number_of_pins:
        try:
            num = int(number_of_pins)
            if num > 0:
                pin_req = PinRequest.objects.create(
                    user=request.user,
                    number_of_pins=num,
                    status='pending'
                )
                response_data['status_code'] = 201
                response_data['message'] = "Pin request submitted successfully"
                response_data['request_id'] = pin_req.id
            else:
                 response_data['status_code'] = 400
                 response_data['message'] = "Number of pins must be positive"
        except ValueError:
             response_data['status_code'] = 400
             response_data['message'] = "Invalid number format"
        except Exception as e:
             response_data['status_code'] = 500
             response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "number_of_pins required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_req_pins = str(uuid.uuid4())
Api.objects.create(
    key=key_req_pins,
    name="Request Pins",
    method="POST",
    content=request_pins_content,
    version=1.0
)
print(f"Created 'Request Pins' API: {key_req_pins}")


# 2. Get Pins List API
get_pins_content = """
from ecommerce_app.models import Pin
from ecommerce_app.serializers import UserSerializer # if needed, can serialize manually

if request.user.is_authenticated:
    # Filter: 'active' or 'all'? Default all or active?
    # Usually show active to redeem.
    status_filter = request.data.get('status') # Optional
    
    pins = Pin.objects.filter(owner=request.user)
    if status_filter:
        pins = pins.filter(status=status_filter)
        
    pins_data = []
    for pin in pins:
        pins_data.append({
            "id": pin.id,
            "code": pin.code,
            "value": float(pin.value),
            "status": pin.status,
            "created_at": pin.created_at.strftime('%Y-%m-%d %H:%M'),
            "used_by": pin.used_by.username if pin.used_by else None,
            "used_at": pin.used_at.strftime('%Y-%m-%d %H:%M') if pin.used_at else None
        })
        
    response_data['status_code'] = 200
    response_data['data'] = pins_data
    response_data['message'] = "Pins fetched successfully"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_get_pins = str(uuid.uuid4())
Api.objects.create(
    key=key_get_pins,
    name="Get Pins",
    method="POST",
    content=get_pins_content,
    version=1.0
)
print(f"Created 'Get Pins' API: {key_get_pins}")


# 3. Redeem Pin API
redeem_pin_content = """
from ecommerce_app.models import Pin, Wallet, Transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

if request.user.is_authenticated:
    pin_id = request.data.get('pin_id')
    target_username = request.data.get('username')
    
    if pin_id and target_username:
        try:
            with transaction.atomic():
                # 1. Validate Pin
                # Pin must belong to request.user (owner) AND be active
                try:
                    pin = Pin.objects.select_for_update().get(id=pin_id, owner=request.user)
                except Pin.DoesNotExist:
                     raise Exception("Pin not found or you do not own it")
                
                if pin.status != 'active':
                    raise Exception("Pin is already used or inactive")
                
                # 2. Validate Target User
                try:
                    target_user = User.objects.get(username=target_username)
                except User.DoesNotExist:
                    raise Exception("Target user not found")
                
                # 3. Process Redemption
                # Update Pin
                pin.status = 'used'
                pin.used_by = target_user
                pin.used_at = timezone.now()
                pin.save()
                
                # Credit Target Wallet
                wallet, _ = Wallet.objects.get_or_create(user=target_user)
                wallet.current_balance += pin.value
                wallet.save()
                
                # Create Transaction for Target User
                Transaction.objects.create(
                    user=target_user,
                    amount=pin.value,
                    direction='deposit',
                    type='pin_credit', # New type
                    description=f"Pin Redeemed by {request.user.username} (Code: {pin.code})"
                )
                
                # Optional: Transaction/History for Sender? 
                # Not strictly a wallet deduction (since pin was asset), but good for records?
                # Prompt says "credit the pin walle in Transaction" (singular). 
                # Assuming credit record for receiver is key.
                
                response_data['status_code'] = 200
                response_data['message'] = "Pin redeemed successfully. Wallet credited."
                response_data['transaction_amount'] = float(pin.value)
                
        except Exception as e:
            response_data['status_code'] = 400
            response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Pin ID and Target Username required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_redeem_pin = str(uuid.uuid4())
Api.objects.create(
    key=key_redeem_pin,
    name="Redeem Pin",
    method="POST",
    content=redeem_pin_content,
    version=1.0
)
print(f"Created 'Redeem Pin' API: {key_redeem_pin}")
