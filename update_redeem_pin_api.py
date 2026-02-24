import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

def main():
    print("Updating 'Redeem Pin' API...")
    api = Api.objects.filter(name="Redeem Pin").first()
    if not api:
        print("Error: 'Redeem Pin' API not found!")
        return

    redeem_pin_content = """from ecommerce_app.models import Pin, Wallet, Transaction, Product, Order, OrderItem
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

if request.user.is_authenticated:
    pin_id = request.data.get('pin_id')
    target_username = request.data.get('username')
    product_id = request.data.get('product_id')
    
    if pin_id and target_username and product_id:
        try:
            with transaction.atomic():
                # 1. Validate Pin
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
                
                # 3. Validate Product
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise Exception("Product not found")

                # 4. Process Redemption
                pin.status = 'used'
                pin.used_by = target_user
                pin.used_at = timezone.now()
                pin.save()
                
                # 5. Credit Target Wallet
                Transaction.objects.create(
                    user=target_user,
                    amount=pin.value,
                    direction='credit',
                    type='deposit', 
                    description=f"Pin Redeemed by {request.user.username} (Code: {pin.code})"
                )
                
                # 6. Checkout Process - Deduct wallet and create Order
                Transaction.objects.create(
                    user=target_user,
                    amount=product.price,
                    direction='debit',
                    type='purchase',
                    description=f"Order Checkout via Pin Redemption for Product ID: {product.id}"
                )

                # Create Order as 'paid' to trigger MLM PV signals
                order = Order.objects.create(
                    user=target_user,
                    total_amount=product.price,
                    total_pv=product.pv,
                    status='paid' 
                )
                
                # Create Order Item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=1,
                    price=product.price,
                    pv=product.pv
                )
                
                response_data['status_code'] = 200
                response_data['message'] = "Pin redeemed and order created successfully."
                response_data['transaction_amount'] = float(pin.value)
                response_data['order_id'] = order.id
                
        except Exception as e:
            response_data['status_code'] = 400
            response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Pin ID, Target Username, and Product ID are required."
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""
    api.content = redeem_pin_content
    # Increment minor version
    api.version = float(api.version) + 0.1
    api.save()

    print(f"Successfully updated 'Redeem Pin' API! New Version: {api.version}")

if __name__ == '__main__':
    main()
