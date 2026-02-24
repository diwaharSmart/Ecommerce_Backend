import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

key_checkout = "24b525f0-5716-43a0-be7f-8566ef74e92e"
checkout_content = """
from ecommerce_app.models import Cart, CartItem, Order, OrderItem, Wallet, Transaction
from django.shortcuts import get_object_or_404

if request.user.is_authenticated:
    try:
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            response_data['status_code'] = 400
            response_data['message'] = "Cart is empty"
        else:
            total_amount = sum(item.total_price for item in cart.items.all())
            total_pv = sum(item.total_pv for item in cart.items.all())
            
            # Check Wallet Balance
            wallet = request.user.wallet
            
            if wallet.current_balance >= total_amount:
                # Deduct Balance
                wallet.current_balance -= total_amount
                wallet.save()
                
                # Create Transaction
                Transaction.objects.create(
                    user=request.user,
                    amount=-total_amount,
                    type='purchase',
                    description=f"Purchase of Order"
                )
                
                # Create Order (Pending)
                order = Order.objects.create(
                    user=request.user,
                    total_amount=total_amount,
                    total_pv=total_pv,
                    status='pending' 
                )
                
                # Create Order Items
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                        pv=item.product.pv
                    )
                
                # Update Status to Paid (Trigger Signal for Coupon Generation)
                order.status = 'paid'
                order.save()
                
                # Clear Cart
                cart.items.all().delete()
                
                # Update Profile (MLM)
                profile = request.user.profile
                profile.package_amount = float(profile.package_amount) + float(total_amount)
                profile.is_active = True
                profile.save()
                
                response_data['status_code'] = 201
                response_data['message'] = "Order created and paid successfully"
                response_data['order_id'] = order.id
            else:
                response_data['status_code'] = 400
                response_data['message'] = "Insufficient Wallet Balance"
                
    except Exception as e:
         response_data['status_code'] = 500
         response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

try:
    # Find by NAME to be safe, or just update the one with the 'current' DB key if known.
    # But finding by Name is safer if we want to force the key.
    api = Api.objects.get(name="Checkout")
    api.key = key_checkout # Force the key to match documentation
    api.content = checkout_content
    api.save()
    print(f"Successfully updated content AND RESTORED Key for Checkout API to: {key_checkout}")
except Api.DoesNotExist:
    print(f"Error: API with name 'Checkout' not found.")

