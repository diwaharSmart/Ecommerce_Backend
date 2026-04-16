import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Profile, Wallet, Transaction
from ecommerce_app.signals import distribute_matching_level_income

def process_binary_match(profile):
    """
    Checks for 1:2 or 2:1 matching (min 100:200).
    Deducts PV and calculates total payout first, then bulk writes to database.
    This prevents O(N) database crashes when processing massive PV increments.
    """
    left = profile.current_left_pv
    right = profile.current_right_pv
    
    total_deduct_left = Decimal("0")
    total_deduct_right = Decimal("0")
    total_matches = 0
    
    # Calculate matches in memory (RAM is fast) instead of writing to DB each iteration
    while True:
        if left >= 200 and right >= 100:
            left -= 100
            right -= 100
            total_deduct_left += 100
            total_deduct_right += 100
            total_matches += 1
        elif left >= 100 and right >= 200:
            left -= 100
            right -= 100
            total_deduct_left += 100
            total_deduct_right += 100
            total_matches += 1
        else:
            break

    if total_matches > 0:
        # Apply bulk deduction mathematically
        profile.current_left_pv -= total_deduct_left
        profile.current_right_pv -= total_deduct_right
        profile.save() # Ensure profile pv changes are strictly saved
        
        # Payout: 100 matched PV (the weak side unit) * 5 Rs = 500 Rs per pair
        total_payout = Decimal(str(total_matches * 500))
        
        # 1. Credit Wallet ONCE
        wallet, _ = Wallet.objects.get_or_create(user=profile.user)
        wallet.current_balance = Decimal(str(wallet.current_balance)) + total_payout
        wallet.save()
        
        # 2. Create Transaction ONCE
        Transaction.objects.create(
            user=profile.user,
            amount=total_payout,
            direction='credit', # Updated deposit to credit based on actual schema usually used
            type='binary_income',
            description=f"Binary match reward for {total_matches} pairs (Deducted L:{total_deduct_left} R:{total_deduct_right})"
        )
        
        # 3. Distribute Matching Level Income ONCE based on total payout
        distribute_matching_level_income(profile, total_payout)
        return total_matches
    return 0

def run_bulk_match():
    print("Starting bulk binary match processing for all profiles...")
    profiles = Profile.objects.all()
    count = 0
    total_pairs_generated = 0
    
    for p in profiles:
        matches = process_binary_match(p)
        if matches > 0:
            count += 1
            total_pairs_generated += matches
            print(f"Processed User {p.user.username}: {matches} pairs matched.")
            
    print("\n--- Bulk Match Complete ---")
    print(f"Profiles updated: {count}")
    print(f"Total pairs matched: {total_pairs_generated}")

if __name__ == '__main__':
    run_bulk_match()
