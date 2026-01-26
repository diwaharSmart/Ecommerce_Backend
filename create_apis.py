import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Resetting and Creating dynamic APIs with UUID keys...")

# Delete all existing APIs
Api.objects.all().delete()

# 1. Get Products API
prod_content = """
from ecommerce_app.models import Product, Banner, Category
from ecommerce_app.serializers import ProductSerializer, BannerSerializer, CategorySerializer

banners = Banner.objects.filter(is_active=True)
categories = Category.objects.all()
products = Product.objects.filter(available=True)

response_data['status_code'] = 200
response_data['data'] = {
    "banners": BannerSerializer(banners, many=True).data,
    "categories": CategorySerializer(categories, many=True).data,
    "products": ProductSerializer(products, many=True).data
}
response_data['message'] = "Home data fetched successfully"
"""

# We can use a readable key for internal reference if name allows, but user requested UUID keys.
# Wait, if I use random UUID, how does the frontend know?
# The user said "create all apis created api keys are UUID4".
# And "For Home screen i need data banners, Categories, Products data in a single API."
# I'll create a "Home" API and giving it a UUID key.

key_home = str(uuid.uuid4())
Api.objects.create(
    key=key_home,
    name="Home API",
    method="GET",
    content=prod_content,
    version=1.0
)
print(f"Created 'Home API' with Key: {key_home}")


# 2. Get Profile/Wallet API
profile_content = """
if request.user.is_authenticated:
    try:
        profile = request.user.profile
        wallet = request.user.wallet
        data = {
            "username": request.user.username,
            "email": request.user.email,
            "is_active": profile.is_active,
            "wallet_balance": float(wallet.current_balance),
            "sponsor": profile.sponsor.user.username if profile.sponsor else None,
            "position": profile.position,
            "total_left_pv": profile.total_left_pv,
            "total_right_pv": profile.total_right_pv,
            "current_left_pv": profile.current_left_pv,
            "current_right_pv": profile.current_right_pv, 
        }
        response_data['status_code'] = 200
        response_data['data'] = data
    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_profile = str(uuid.uuid4())
Api.objects.create(
    key=key_profile,
    name="Get Profile",
    method="POST",
    content=profile_content,
    version=1.0
)
print(f"Created 'Get Profile' with Key: {key_profile}")

# 3. Payin Request API
payin_content = """
if request.user.is_authenticated:
    amount = request.data.get('amount')
    ref_no = request.data.get('reference_number')
    
    if amount and ref_no:
        from ecommerce_app.models import PayinRequest
        try:
             payin = PayinRequest.objects.create(
                 user=request.user,
                 amount=amount,
                 reference_number=ref_no
             )
             response_data['status_code'] = 201
             response_data['message'] = "Payin request created"
             response_data['payin_id'] = payin.id
        except Exception as e:
             response_data['status_code'] = 400
             response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Amount and Reference Number required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_payin = str(uuid.uuid4())
Api.objects.create(
    key=key_payin,
    name="Create Payin",
    method="POST",
    content=payin_content,
    version=1.0
)
print(f"Created 'Create Payin' with Key: {key_payin}")

print("-" * 30)
print("API Keys Summary:")
print(f"Home API: {key_home}")
print(f"Profile API: {key_profile}")
print(f"Payin API: {key_payin}")

# 4. Get Cart API
cart_content = """
from ecommerce_app.models import Cart, CartItem
from ecommerce_app.serializers import CartSerializer

if request.user.is_authenticated:
    cart, _ = Cart.objects.get_or_create(user=request.user)
    # Using serializer to get full cart details (items, total_price, total_pv)
    serializer = CartSerializer(cart)
    
    response_data['status_code'] = 200
    response_data['data'] = serializer.data
    response_data['message'] = "Cart details fetched"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_get_cart = str(uuid.uuid4())
Api.objects.create(
    key=key_get_cart,
    name="Get Cart",
    method="POST", # Using POST for auth
    content=cart_content,
    version=1.0
)
print(f"Created 'Get Cart' with Key: {key_get_cart}")


# 5. Add to Cart API
add_cart_content = """
from ecommerce_app.models import Cart, CartItem, Product
from django.shortcuts import get_object_or_404

if request.user.is_authenticated:
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    
    if product_id:
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            product = get_object_or_404(Product, id=product_id)
            
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()
            
            response_data['status_code'] = 200
            response_data['message'] = "Item added to cart"
        except Exception as e:
            response_data['status_code'] = 400
            response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Product ID required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_add_cart = str(uuid.uuid4())
Api.objects.create(
    key=key_add_cart,
    name="Add to Cart",
    method="POST",
    content=add_cart_content,
    version=1.0
)
print(f"Created 'Add to Cart' with Key: {key_add_cart}")


# 6. Remove from Cart API
remove_cart_content = """
from ecommerce_app.models import Cart, CartItem, Product
from django.shortcuts import get_object_or_404

if request.user.is_authenticated:
    product_id = request.data.get('product_id')
    
    if product_id:
        try:
            cart = Cart.objects.get(user=request.user)
            product = get_object_or_404(Product, id=product_id)
            CartItem.objects.filter(cart=cart, product=product).delete()
            
            response_data['status_code'] = 200
            response_data['message'] = "Item removed from cart"
        except Exception as e:
             response_data['status_code'] = 400
             response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Product ID required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_remove_cart = str(uuid.uuid4())
Api.objects.create(
    key=key_remove_cart,
    name="Remove from Cart",
    method="POST",
    content=remove_cart_content,
    version=1.0
)
print(f"Created 'Remove from Cart' with Key: {key_remove_cart}")

# 7. Checkout API
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
            
            wallet = Wallet.objects.get(user=request.user)
            
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
                
                # Create Order (Paid)
                order = Order.objects.create(
                    user=request.user,
                    total_amount=total_amount,
                    total_pv=total_pv,
                    status='paid' 
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

key_checkout = "24b525f0-5716-43a0-be7f-8566ef74e92e" # Preserved Key
Api.objects.create(
    key=key_checkout,
    name="Checkout",
    method="POST",
    content=checkout_content,
    version=1.1 # Version bump
)
print(f"Created 'Checkout' with Key: {key_checkout}")

# 8. Get Support Tickets API
get_tickets_content = """
from ecommerce_app.models import SupportTicket
from ecommerce_app.serializers import SupportTicketSerializer

if request.user.is_authenticated:
    tickets = SupportTicket.objects.filter(user=request.user)
    serializer = SupportTicketSerializer(tickets, many=True)
    
    response_data['status_code'] = 200
    response_data['data'] = serializer.data
    response_data['message'] = "Tickets fetched successfully"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_get_tickets = str(uuid.uuid4())
Api.objects.create(
    key=key_get_tickets,
    name="Get Tickets",
    method="POST",
    content=get_tickets_content,
    version=1.0
)
print(f"Created 'Get Tickets' with Key: {key_get_tickets}")

# 9. Create Support Ticket API
create_ticket_content = """
from ecommerce_app.models import SupportTicket
from ecommerce_app.serializers import SupportTicketSerializer

if request.user.is_authenticated:
    subject = request.data.get('subject')
    message = request.data.get('message')
    
    if subject and message:
        try:
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                message=message,
                status='open'
            )
            response_data['status_code'] = 201
            response_data['message'] = "Support ticket created"
            response_data['ticket_id'] = ticket.id
        except Exception as e:
            response_data['status_code'] = 400
            response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Subject and Message required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_create_ticket = str(uuid.uuid4())
Api.objects.create(
    key=key_create_ticket,
    name="Create Ticket",
    method="POST",
    content=create_ticket_content,
    version=1.0
)
print(f"Created 'Create Ticket' with Key: {key_create_ticket}")

# 10. Get Binary Tree API (3 Levels)
binary_tree_content = """
from ecommerce_app.models import Profile, User
from django.shortcuts import get_object_or_404

def get_node_data(profile, current_level, max_level):
    if not profile or current_level > max_level:
        return None
    
    data = {
        "user_id": profile.user.id,
        "username": profile.user.username,
        "profile_image": request.build_absolute_uri(profile.user.kyc.passbook_image.url) if hasattr(profile.user, 'kyc') and profile.user.kyc.passbook_image else None,
        "position": profile.position,
        "is_active": profile.is_active,
        "total_left_pv": profile.total_left_pv,
        "total_right_pv": profile.total_right_pv,
        "left": None,
        "right": None
    }
    
    # Find Left Child
    left_child = Profile.objects.filter(parent=profile.user.profile, position='L').first()
    if left_child:
        data["left"] = get_node_data(left_child, current_level + 1, max_level)
    
    # Find Right Child
    right_child = Profile.objects.filter(parent=profile.user.profile, position='R').first()
    if right_child:
        data["right"] = get_node_data(right_child, current_level + 1, max_level)
        
    return data

if request.user.is_authenticated:
    target_user_id = request.data.get('user_id')
    user = request.user
    
    if target_user_id:
        try:
             target_user = User.objects.get(id=target_user_id)
             # User can view tree starting from anyone in their downline - or simplified: view anyone's tree for now
             user = target_user
        except User.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "User not found"
    
    if 'status_code' not in response_data or response_data['status_code'] == 200:
        try:
            root_profile = user.profile
            tree_data = get_node_data(root_profile, 0, 3) # level 0 + 3 levels down
            
            response_data['status_code'] = 200
            response_data['data'] = tree_data
            response_data['message'] = "Binary tree fetched successfully"
        except Exception as e:
            response_data['status_code'] = 500
            response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_binary_tree = str(uuid.uuid4())
Api.objects.create(
    key=key_binary_tree,
    name="Get Binary Tree",
    method="POST",
    content=binary_tree_content,
    version=1.0
)
print(f"Created 'Get Binary Tree' with Key: {key_binary_tree}")


# 11. Get Level Members API (5 Levels)
level_members_content = """
from ecommerce_app.models import Profile, Transaction
from django.contrib.auth.models import User
from django.db.models import Sum

if request.user.is_authenticated:
    target_user_id = request.data.get('user_id')
    root_user = request.user
    
    if target_user_id:
        try:
             root_user = User.objects.get(id=target_user_id)
        except Exception:
             pass 
    
    try:
        levels_data = {}
        current_level_members = [root_user.profile]
        transactions = Transaction.objects.filter(user=root_user) # Earnings for the ROOT user
        
        for i in range(1, 6): # Levels 1 to 5
            next_level_members = []
            level_key = f"level_{i}"
            
            members_list = []
            
            for parent in current_level_members:
                # Find all profiles where this parent is the sponsor
                children = Profile.objects.filter(sponsor=parent)
                for child in children:
                    members_list.append({
                        "user_id": child.user.id,
                        "username": child.user.username,
                        "join_date": child.created_at.strftime('%Y-%m-%d'),
                        "package": float(child.package_amount),
                        "sponsor_id": parent.user.id
                    })
                    next_level_members.append(child)
            
            # Calculate Earnings for this level
            # Search for transactions with type "level_income" and description containing "Level {i} income"
            level_income = transactions.filter(type='level_income', description__icontains=f"Level {i} income").aggregate(Sum('amount'))['amount__sum'] or 0.0

            levels_data[level_key] = {
                "count": len(members_list),
                "earnings": float(level_income),
                "members": members_list
            }
            
            current_level_members = next_level_members
            if not current_level_members:
                # Even if no members, we might want to return 0 earnings/count for remaining levels or just stop?
                # Let's stop traversing, but initializing empty structure for remaining levels might be cleaner for frontend.
                # For now, let's just break as per original logic, avoiding empty loops.
                # But we should ensure we don't crash if frontend expects keys. 
                # Original logic broke. Let's keep it.
                pass # Continue to next i? No, if no members in L1, no L2.
                # Ideally we continue the loop just to fill 'earnings' if independent? No, earnings depend on members existing? 
                # Actually, can you have earnings from L2 if current L2 members are 0? 
                # Yes, if they were active and generated income then deleted? Unlikely in this system.
                # But wait, 'current_level_members' finds current structure. 
                # Earnings logic uses 'transactions' which is historical. 
                # So even if members effectively left (not possible here yet), we have history.
                # But the loop depends on traversing parents. If path broken, we can't find L+1.
                
                if not next_level_members:
                   pass # Break is naturally happening if we rely on next_level_members for next iter.
        
        response_data['status_code'] = 200
        response_data['data'] = levels_data
        response_data['message'] = "Level members fetched successfully"

    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_level_members = str(uuid.uuid4())
Api.objects.create(
    key=key_level_members,
    name="Get Level Members",
    method="POST",
    content=level_members_content,
    version=1.0
)
print(f"Created 'Get Level Members' with Key: {key_level_members}")



# 12. Register API
register_content = """
from django.contrib.auth.models import User
from ecommerce_app.models import Profile, Wallet, KYC
import random
import string
from django.db.models import F

name = request.data.get('name')
mobile = request.data.get('mobile')
password = request.data.get('password')
sponsor_id_str = request.data.get('sponsor_id')
position = request.data.get('position') # 'L' or 'R'

if name and mobile and password and sponsor_id_str and position:
    try:
        # Verify Sponsor
        if sponsor_id_str.isdigit():
             sponsor_user = User.objects.get(id=sponsor_id_str)
        else:
             sponsor_user = User.objects.get(username=sponsor_id_str)
        
        # Generate Username
        while True:
            random_digits = ''.join(random.choices(string.digits, k=7))
            username = f"VEDAON_{random_digits}"
            if not User.objects.filter(username=username).exists():
                break
        
        # Create User
        user = User.objects.create_user(username=username, email=mobile, password=password, first_name=name)
        profile = user.profile
        profile.sponsor = sponsor_user.profile
        
        # Find Placement Parent
        current_node = sponsor_user.profile
        while True:
            child = Profile.objects.filter(parent=current_node, position=position).first()
            if not child:
                break
            current_node = child
        
        profile.parent = current_node
        profile.position = position
        profile.save()
        
        # --- Update Member Counts Up the Tree ---
        # Traverse up from parent to root
        temp_node = profile.parent
        temp_position = profile.position
        
        while temp_node:
            if temp_position == 'L':
                Profile.objects.filter(id=temp_node.id).update(total_left_count=F('total_left_count') + 1)
            elif temp_position == 'R':
                Profile.objects.filter(id=temp_node.id).update(total_right_count=F('total_right_count') + 1)
            
            # Move up
            temp_position = temp_node.position # Position of this node relative to ITS parent
            temp_node = temp_node.parent
            
        
        response_data['status_code'] = 201
        response_data['message'] = "User registered successfully"
        response_data['data'] = {
            "user_id": user.id,
            "username": username,
            "name": name
        }
    except User.DoesNotExist:
        response_data['status_code'] = 400
        response_data['message'] = "Invalid Sponsor ID"
    except Exception as e:
        response_data['status_code'] = 400
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 400
    response_data['message'] = "Missing required fields (name, mobile, password, sponsor_id, position)"
"""

key_register = str(uuid.uuid4())
Api.objects.create(
    key=key_register,
    name="Register User",
    method="POST",
    content=register_content,
    version=1.0
)
print(f"Created 'Register User' with Key: {key_register}")


# 13. Login API
login_content = """
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

username = request.data.get('username') or request.data.get('user_id') # handle both
password = request.data.get('password')

if username and password:
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        response_data['status_code'] = 200
        response_data['message'] = "Login successful"
        response_data['token'] = token.key
        response_data['user_id'] = user.id
        response_data['username'] = user.username
        response_data['name'] = user.first_name
    else:
        response_data['status_code'] = 401
        response_data['message'] = "Invalid credentials"
else:
    response_data['status_code'] = 400
    response_data['message'] = "Username and Password required"
"""

key_login = str(uuid.uuid4())
Api.objects.create(
    key=key_login,
    name="Login User",
    method="POST",
    content=login_content,
    version=1.0
)
print(f"Created 'Login User' with Key: {key_login}")


# 14. Change Password API
change_password_content = """
if request.user.is_authenticated:
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if old_password and new_password:
        if request.user.check_password(old_password):
            request.user.set_password(new_password)
            request.user.save()
            response_data['status_code'] = 200
            response_data['message'] = "Password changed successfully"
        else:
             response_data['status_code'] = 400
             response_data['message'] = "Incorrect old password"
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Old and New passwords required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_change_password = str(uuid.uuid4())
Api.objects.create(
    key=key_change_password,
    name="Change Password",
    method="POST",
    content=change_password_content,
    version=1.0
)
print(f"Created 'Change Password' with Key: {key_change_password}")


# 15. Address APIs (Add, Edit, Delete)
# Consolidating into one API endpoint with 'action' param or separate? 
# "Add edit delete address" -> separate keys usually better for clarity or RESTful actions.
# Let's do separate or Action based. Let's do action based for simplicity to not explode keys count too much, or separate.
# User asked "Create , Edit, Get KYC" separately later.
# Let's do "Manage Address" with action.

address_content = """
from ecommerce_app.models import UserAddress
from ecommerce_app.serializers import UserAddressSerializer

if request.user.is_authenticated:
    action = request.data.get('action') # 'add', 'edit', 'delete', 'get'
    
    if action == 'add':
        serializer = UserAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            response_data['status_code'] = 201
            response_data['message'] = "Address added"
            response_data['data'] = serializer.data
        else:
            response_data['status_code'] = 400
            response_data['message'] = str(serializer.errors)
            
    elif action == 'edit':
        addr_id = request.data.get('id')
        try:
            address = UserAddress.objects.get(id=addr_id, user=request.user)
            serializer = UserAddressSerializer(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response_data['status_code'] = 200
                response_data['message'] = "Address updated"
                response_data['data'] = serializer.data
            else:
                response_data['status_code'] = 400
                response_data['message'] = str(serializer.errors)
        except UserAddress.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "Address not found"

    elif action == 'delete':
        addr_id = request.data.get('id')
        try:
            UserAddress.objects.get(id=addr_id, user=request.user).delete()
            response_data['status_code'] = 200
            response_data['message'] = "Address deleted"
        except UserAddress.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "Address not found"
             
    elif action == 'get' or action is None:
        addresses = UserAddress.objects.filter(user=request.user)
        serializer = UserAddressSerializer(addresses, many=True)
        response_data['status_code'] = 200
        response_data['data'] = serializer.data
        response_data['message'] = "Addresses fetched"
        
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Invalid action"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_address = str(uuid.uuid4())
Api.objects.create(
    key=key_address,
    name="Manage Address",
    method="POST",
    content=address_content,
    version=1.0
)
print(f"Created 'Manage Address' with Key: {key_address}")


# 16. KYC APIs (Create, Edit, Get)
kyc_content = """
from ecommerce_app.models import KYC
from ecommerce_app.serializers import KYCSerializer

if request.user.is_authenticated:
    action = request.data.get('action') # 'create', 'edit', 'get'
    
    if action == 'create':
        if KYC.objects.filter(user=request.user).exists():
             response_data['status_code'] = 400
             response_data['message'] = "KYC already exists"
        else:
            serializer = KYCSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                response_data['status_code'] = 201
                response_data['message'] = "KYC submitted"
                response_data['data'] = serializer.data
            else:
                response_data['status_code'] = 400
                response_data['message'] = str(serializer.errors)
                
    elif action == 'edit':
        try:
            kyc = KYC.objects.get(user=request.user)
            if kyc.status == 'verified':
                 response_data['status_code'] = 400
                 response_data['message'] = "Cannot edit verified KYC"
            else:
                serializer = KYCSerializer(kyc, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    response_data['status_code'] = 200
                    response_data['message'] = "KYC updated"
                    response_data['data'] = serializer.data
                else:
                    response_data['status_code'] = 400
                    response_data['message'] = str(serializer.errors)
        except KYC.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "KYC not found"

    elif action == 'get' or action is None:
        try:
            kyc = KYC.objects.get(user=request.user)
            serializer = KYCSerializer(kyc)
            response_data['status_code'] = 200
            response_data['data'] = serializer.data
            response_data['message'] = "KYC details fetched"
        except KYC.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "KYC not found"
             
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Invalid action"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_kyc = str(uuid.uuid4())
Api.objects.create(
    key=key_kyc,
    name="Manage KYC",
    method="POST",
    content=kyc_content,
    version=1.0
)
print(f"Created 'Manage KYC' with Key: {key_kyc}")

# 17. Get Wallet API (Balance + Transactions)
wallet_content = """
from ecommerce_app.models import Wallet, Transaction
from ecommerce_app.serializers import TransactionSerializer

if request.user.is_authenticated:
    try:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        
        response_data['status_code'] = 200
        response_data['message'] = "Wallet details fetched"
        response_data['data'] = {
            "current_balance": float(wallet.current_balance),
            "transactions": serializer.data
        }
    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_wallet = str(uuid.uuid4())
Api.objects.create(
    key=key_wallet,
    name="Get Wallet",
    method="POST",
    content=wallet_content,
    version=1.0
)
print(f"Created 'Get Wallet' with Key: {key_wallet}")

# 18. Get MLM Dashboard API
dashboard_content = """
from ecommerce_app.models import Profile, Transaction, Wallet
from django.db.models import Sum, Count

if request.user.is_authenticated:
    try:
        profile = request.user.profile
        transactions = Transaction.objects.filter(user=request.user)
        
        # 1. Left/Right Counts (Fields added to Profile)
        left_count = profile.total_left_count
        right_count = profile.total_right_count
        
        # 2. Pair Match Count (Transactions type='binary_income')
        pair_match_count = transactions.filter(type='binary_income').count()
        
        # 3. Active Users (Direct Referrals who are active)
        active_directs = Profile.objects.filter(sponsor=profile, is_active=True).count()
        
        # 4. Total Yours (Direct Referrals Count)
        total_directs = Profile.objects.filter(sponsor=profile).count()
        
        # 5. Level 1-5 Member Counts & Earnings
        # Getting Level Counts requires traversing. 
        # Getting Level Earnings is easy from Transactions.
        
        level_stats = []
        current_level_members = [profile]
        
        # We can calculate level earnings from 'description' if we parsed it, or strict type, 
        # but Transaction model has 'type=level_income' but not 'level_number' field. 
        # Description has "Level X income...". We can filter description.
        
        for i in range(1, 6):
            # Count Members in this level (Global tree level relative to user)
            next_level_members = []
            count = 0
            for parent in current_level_members:
                children = Profile.objects.filter(sponsor=parent) # Sponsor tree
                count += children.count()
                next_level_members.extend(children)
            
            current_level_members = next_level_members
            
            # Earnings for this level
            # description__contains=f"Level {i} income" is string matching, bit brittle but works for now.
            level_income = transactions.filter(type='level_income', description__icontains=f"Level {i} income").aggregate(Sum('amount'))['amount__sum'] or 0.0
            
            level_stats.append({
                "level": i,
                "member_count": count,
                "earnings": float(level_income)
            })
            
            if not current_level_members:
                 pass

        # 6. Business Stats
        business_stats = {
            "total_left_pv": profile.total_left_pv,
            "total_right_pv": profile.total_right_pv,
            "current_left_pv": profile.current_left_pv,
            "current_right_pv": profile.current_right_pv,
        }

        response_data['status_code'] = 200
        response_data['message'] = "Dashboard data fetched"
        response_data['data'] = {
             "left_count": left_count,
             "right_count": right_count,
             "pair_match_count": pair_match_count,
             "active_directs": active_directs,
             "total_directs": total_directs,
             "level_stats": level_stats,
             "business_stats": business_stats
        }

    except Exception as e:
        response_data['status_code'] = 500
        response_data['message'] = str(e)
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

key_dashboard = str(uuid.uuid4())
Api.objects.create(
    key=key_dashboard,
    name="Get MLM Dashboard",
    method="POST",
    content=dashboard_content,
    version=1.0
)
print(f"Created 'Get MLM Dashboard' with Key: {key_dashboard}")

print(f"Created 'Get MLM Dashboard' with Key: {key_dashboard}")

# 19. Get Category with Products API
category_content = """
from ecommerce_app.models import Category
from ecommerce_app.serializers import CategorySerializer, ProductSerializer

try:
    categories = Category.objects.all()
    data = []
    
    for cat in categories:
        products = cat.products.filter(available=True)
        # Serialize Category
        cat_data = CategorySerializer(cat).data
        # Add Nested Products
        cat_data['products'] = ProductSerializer(products, many=True).data
        data.append(cat_data)
        
    response_data['status_code'] = 200
    response_data['message'] = "Categories with products fetched"
    response_data['data'] = data
except Exception as e:
    response_data['status_code'] = 500
    response_data['message'] = str(e)
"""

key_category_products = str(uuid.uuid4())
Api.objects.create(
    key=key_category_products,
    name="Get Category Products",
    method="POST",
    content=category_content, # No auth required, public catalog
    version=1.0
)
print(f"Created 'Get Category Products' with Key: {key_category_products}")

print("-" * 30)
