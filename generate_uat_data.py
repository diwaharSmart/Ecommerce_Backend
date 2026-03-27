import os
import django
import sys
import uuid
import random
from collections import deque
from decimal import Decimal

# Force SQLite UAT
os.environ['USE_UAT_DB'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from ecommerce_app.models import Profile, Product, Order, OrderItem, Transaction, Wallet

def generate_username(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def run_generator(target_users=100):
    print(f"Starting Real-World Flow UAT Generation for {target_users} users...")
    
    try:
        sea_buckthorn = Product.objects.get(id=23)
        grocery_coupon = Product.objects.get(id=53)
        products = [sea_buckthorn, grocery_coupon]
    except Product.DoesNotExist:
        print("Error: Products not found.")
        return

    # Pre-hash password so we don't spend 3 hours calculating cryptograhpic SHA256 hashes 100,000 times
    print("Pre-calculating cryptographic hashes...")
    fast_hash = make_password('123456')

    # Base Root Logic
    company_profiles = []
    
    print("Checking/Creating Golden Triangle...")
    if not User.objects.filter(username__startswith='company_uat').exists():
        for i in range(1, 4):
            u = User(username=f"company_uat_{i}", password=fast_hash, first_name='Company', last_name=f'Node {i}')
            u.save() # Triggers profile & wallet creation
            company_profiles.append(u.profile)
            
        root = company_profiles[0]
        left = company_profiles[1]
        right = company_profiles[2]
        
        left.parent = root
        left.sponsor = root
        left.position = 'L'
        left.save()
        
        right.parent = root
        right.sponsor = root
        right.position = 'R'
        right.save()
        
        # Activate roots
        for p in company_profiles:
            simulate_user_purchase_flow(p.user, products[0])
            
    # Load queue with available parent spots
    queue = deque()
    all_profiles = Profile.objects.all().order_by('id')
    for p in all_profiles:
        children_count = Profile.objects.filter(parent=p).count()
        if children_count < 2:
            queue.append(p)

    users_created = 0
    total_revenue = Decimal('0.00')

    print(f"Queue populated. Starting continuous real-world insertion loop...")
    from django.db import transaction

    while users_created < target_users:
        batch_size = min(1000, target_users - users_created)
        
        with transaction.atomic():
            for _ in range(batch_size):
                u = User(
                    username=generate_username("user"), 
                    password=fast_hash,
                    first_name=f'UAT',
                    last_name=f'User {users_created+1}'
                )
                u.save() # Mapped to SQLite instance immediately
                
                profile = u.profile
                parent_profile = queue[0]
                
                if not Profile.objects.filter(parent=parent_profile, position='L').exists():
                    profile.position = 'L'
                elif not Profile.objects.filter(parent=parent_profile, position='R').exists():
                    profile.position = 'R'
                    queue.popleft()
                else:
                    queue.popleft()
                    u.delete()
                    continue
                    
                profile.parent = parent_profile
                profile.sponsor = parent_profile
                profile.save()
                queue.append(profile)
                
                # Activate User using REAL WORLD FLOW
                prod = random.choice(products)
                simulate_user_purchase_flow(u, prod)
                
                users_created += 1
                total_revenue += prod.price
                
        print(f"Committed block of {batch_size}. Total Progress: {users_created}/{target_users} users")

    print(f"\n[SUCCESS] Generator Sequence Completed.")

def simulate_user_purchase_flow(user, prod):
    """
    Exactly mimics what a user does on the frontend:
    1. Deposit funds.
    2. Purchase order.
    3. Order completes -> Signals activate MLM.
    """
    wallet = user.wallet
    
    # 1. Deposit 3000
    wallet.current_balance = Decimal(str(wallet.current_balance)) + Decimal(str(prod.price))
    wallet.save()
    Transaction.objects.create(
        user=user, amount=prod.price, 
        direction='deposit', type='deposit', description="Initial UAT Wallet Deposit"
    )
    
    # 2. Purchase Package
    wallet.current_balance = Decimal(str(wallet.current_balance)) - Decimal(str(prod.price))
    wallet.save()
    Transaction.objects.create(
        user=user, amount=-prod.price, 
        direction='withdrawal', type='purchase', description="Purchase of Order"
    )
    
    # 3. Create and Paid Order
    order = Order.objects.create(user=user, total_amount=prod.price, total_pv=prod.pv, status='pending')
    OrderItem.objects.create(order=order, product=prod, price=prod.price, pv=prod.pv, quantity=1)
    
    # This securely triggers 'signals.py' exact logic
    order.status = 'paid'
    order.save() 

if __name__ == '__main__':
    target = 1000
    if len(sys.argv) > 1:
        target = int(sys.argv[1])
    run_generator(target)
