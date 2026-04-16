import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Transaction

def find_anomalous_binary_transactions():
    print("Querying production database for binary income transactions...")
    transactions = Transaction.objects.filter(type='binary_income').order_by('id')
    
    found_count = 0
    for t in transactions:
        desc = t.description
        # We are looking for "Deducted L:200" or "R:200", etc.
        # The exact string format is usually "(Deducted L:100 R:100)"
        match = re.search(r'Deducted L:(\d+) R:(\d+)', desc)
        if match:
            deduct_l = int(match.group(1))
            deduct_r = int(match.group(2))
            
            if deduct_l == 200 or deduct_r == 200:
                print(f"Txn ID: {t.id} | User: {t.user.username} | Amount: {t.amount} | Desc: {desc}")
                found_count += 1
        elif '200' in desc: # Fallback in case regex fails
             print(f"Txn ID: {t.id} | User: {t.user.username} | Amount: {t.amount} | Desc: {desc}")
             found_count += 1

    print(f"\nTotal matches found: {found_count}")

if __name__ == '__main__':
    find_anomalous_binary_transactions()
