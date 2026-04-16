import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Transaction, Profile
from django.db import transaction as db_transaction

def fix_pv_anomaly():
    print("Fixing PV anomaly on production database...")
    transactions = Transaction.objects.filter(type='binary_income').order_by('id')
    
    fixed_count_l = 0
    fixed_count_r = 0
    users_affected = set()

    with db_transaction.atomic():
        for t in transactions:
            desc = t.description
            match = re.search(r'Deducted L:(\d+) R:(\d+)', desc)
            if match:
                deduct_l = int(match.group(1))
                deduct_r = int(match.group(2))
                
                profile = t.user.profile
                updated = False
                
                if deduct_l == 200:
                    profile.current_left_pv += 100
                    fixed_count_l += 1
                    updated = True
                
                if deduct_r == 200:
                    profile.current_right_pv += 100
                    fixed_count_r += 1
                    updated = True
                    
                if updated:
                    profile.save()
                    users_affected.add(t.user.id)
                    print(f"Fixed Txn #{t.id} - Added PV for {t.user.username} (L: +{100 if deduct_l==200 else 0}, R: +{100 if deduct_r==200 else 0})")

    print(f"\nAnomaly Fix Complete.")
    print(f"Total Left PV additions (+100 L): {fixed_count_l}")
    print(f"Total Right PV additions (+100 R): {fixed_count_r}")
    print(f"Total Unique Users Updated: {len(users_affected)}")

if __name__ == '__main__':
    fix_pv_anomaly()
