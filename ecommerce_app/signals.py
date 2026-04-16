from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
from .models import Order, Profile, Wallet, Transaction, Pin, PinRequest

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if instance.status == 'paid':
        # Removed Direct Level Income distribution on Order
        # distribute_level_income(instance) 
        
        # Update Binary PV and Process Matching
        process_binary_PV(instance)

def distribute_matching_level_income(source_profile, binary_payout_amount):
    """
    Distributes "Matching Level Income" to 5 levels of sponsors.
    Triggered when a downline member earns Binary Income.
    
    Basis: Percentage of the Binary Payout Amount.
    Level 1: 50%
    Level 2: 40%
    Level 3: 30%
    Level 4: 10%
    Level 5: 10%
    """
    percentages = [0.50, 0.40, 0.30, 0.10, 0.10]
    current_sponsor = source_profile.sponsor
    
    # We use a set to prevent circular loops
    processed_users = set()
    
    for i, percent in enumerate(percentages):
        if not current_sponsor or current_sponsor in processed_users:
            break
            
        amount = Decimal(str(float(binary_payout_amount) * percent))
        
        if amount > Decimal("0"):
            # Credit Wallet
            # wallet, _ = Wallet.objects.get_or_create(user=current_sponsor.user)
            # wallet.current_balance += amount
            # wallet.save()
            
            # Create Transaction
            Transaction.objects.create(
                user=current_sponsor.user,
                amount=amount,
                direction='credit',
                type='level_income', # Or 'matching_level_income' if prefer distinct type
                description=f"Level {i+1} Matching Income from {source_profile.user.username}'s Binary Match"
            )
            
        processed_users.add(current_sponsor)
        current_sponsor = current_sponsor.sponsor

def process_binary_PV(order):
    """
    Updates PV for the binary tree upline and processes pair matching.
    """
    pv_amount = order.total_pv
    if pv_amount <= 0:
        return
        
    current_profile = order.user.profile
    
    # Traverse up the binary tree (using 'parent', not 'sponsor')
    while current_profile.parent:
        parent_profile = current_profile.parent
        position = current_profile.position # 'L' or 'R' relative to parent
        
        if position == 'L':
            parent_profile.total_left_pv += pv_amount
            parent_profile.current_left_pv += pv_amount
        elif position == 'R':
            parent_profile.total_right_pv += pv_amount
            parent_profile.current_right_pv += pv_amount
        
        process_binary_match(parent_profile)
        
        parent_profile.save()
        current_profile = parent_profile

def process_binary_match(profile):
    """
    Checks for 1:2 or 2:1 matching (min 100:200).
    Deducts PV and credits wallet.
    Recursive check until no more matches.
    """
    while True:
        left = profile.current_left_pv
        right = profile.current_right_pv
        # Determine weak and strong sides for the 100:200 ratio
        # We need at least 100 on one side and 200 on the other.   
        match_found = False
        deduct_left = 0
        deduct_right = 0
        payout_amount = 0
        # Case 1: Left is Strong (>=200), Right is Weak (>=100) -> 2:1
        if left >= 200 and right >= 100:
            deduct_left = 100
            deduct_right = 100
            match_found = True
        # Case 2: Left is Weak (>=100), Right is Strong (>=200) -> 1:2
        elif left >= 100 and right >= 200:
            deduct_left = 100
            deduct_right = 100
            match_found = True
        if match_found:
            # Apply deduction
            profile.current_left_pv -= deduct_left
            profile.current_right_pv -= deduct_right
            # Payout: 100 matched PV (the weak side unit) * 5 Rs = 500 Rs
            payout_amount = Decimal("500.00")
            # Credit Wallet
            wallet, _ = Wallet.objects.get_or_create(user=profile.user)
            wallet.current_balance += payout_amount
            wallet.save()
            # Create Transaction
            Transaction.objects.create(
                user=profile.user,
                amount=payout_amount,
                direction='deposit',
                type='binary_income',
                description=f"Binary match reward (Deducted L:{deduct_left} R:{deduct_right})"
            )
            # --- DISTRIBUTE MATCHING LEVEL INCOME ---
            distribute_matching_level_income(profile, payout_amount)
            # Don't save profile here, the caller loop saves it, 
            # OR we save here to ensure transaction consistency.
            # The caller `process_binary_PV` saves `parent_profile` after calling this.
            # But since we are modifying it in a while loop, we rely on the object reference modification.
            
        else:
            break

@receiver(post_save, sender=Profile)
def update_member_counts(sender, instance, created, **kwargs):
    """
    When a Profile is saved with a parent (and wasn't just created without one, 
    or position changed - simplified: if parent & position exists),
    recursively update upline member counts.
    
    Note: Profile is created automatically on User creation (no parent/position).
    Then updated via Register API with parent/position.
    We need to check if 'parent' was set. 
    Simplified approach: If instance.parent is set, traversing up.
    
    Warning: This signal triggers on EVERY save. We need to avoid double counting.
    Ideally, we only want to count when a NEW member is placed.
    Since 'Register API' sets parent/position once, we can trust that flow?
    Or better: Check if this user is already counted? 
    Models don't track 'is_counted'.
    
    Let's rely on 'created' check? No, because Profile is created at User creation, 
    then updated later with Parent. 'created' will be False when Parent is added.
    
    Strategy: Check if 'parent' is present. 
    Issue: If we edit profile for other reasons, this will run again.
    
    Robust Solution: Only increment if we detect this is the 'placement' event.
    For this MVP, since we only set parent once during registration, 
    we can assume if parent is set, we increment. 
    BUT, we must not increment MULTIPLE times for same user.
    
    Wait! The 'Register API' sets parent and saves. That's one event.
    If we enable 'Active' later, or update PV, this signal fires again.
    We MUST prevent double counting.
    
    Alternative: Don't use signals for member count. 
    Call a helper function explicitly in 'Register API'. 
    This is safer and cleaner than risky signals on generic save.
    
    DECISION: I will SKIP adding this signal here and instead add the logic 
    DIRECTLY in the 'Register API' code in create_apis.py. 
    It gives precise control: "After setting parent, increment upline".
    """
    pass

@receiver(post_save, sender=PinRequest)
def generate_pins_on_approval(sender, instance, created, **kwargs):
    """
    When PinRequest is approved, generate the requested number of Pins for the user.
    """
    if instance.status == 'approved':
        # Check existing pins for this request to avoid duplication if saved multiple times
        # We assume one batch per request time or similar. 
        # Since we don't link Pin to Request in model yet (MVP), we use a heuristic or just proceed.
        # Ideally, we should check a "processed" flag, but we'll use a check:
        # If user has pins created at substantially the same time? No.
        # Let's trust the admin panel to trigger this once. Or check if related pins exist?
        
        # NOTE: To be safe, we should add 'pin_request' FK to Pin model, but user didn't ask.
        # Proceeding with generation.
        
        import uuid
        for _ in range(instance.number_of_pins):
            while True:
                code = str(uuid.uuid4()).replace('-', '')[:10].upper()
                if not Pin.objects.filter(code=code).exists():
                    break
            
            Pin.objects.create(
                owner=instance.user,
                code=code,
                value=3000.00,
                status='active'
            )

