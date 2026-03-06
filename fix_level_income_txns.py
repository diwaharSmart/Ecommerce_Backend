import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Transaction, Wallet

def main():
    print("Starting correction of Level Income transactions...")
    
    # 1. Find all 'level_income' transactions that were incorrectly marked as 'debit'
    incorrect_txns = Transaction.objects.filter(type='level_income', direction='debit')
    
    count = 0
    total_amount_corrected = Decimal('0.00')
    
    for txn in incorrect_txns:
        user = txn.user
        amount = txn.amount
        
        # We need to correct two things:
        # A) Update the transaction itself to be a 'credit'
        txn.direction = 'credit'
        txn.save(update_fields=['direction'])
        
        # B) The signal creates the transaction. In the buggy code, the wallet was credited 
        # (wallet.current_balance += amount), BUT the transaction was logged as a debit.
        # However, we ALSO have a signal in models.py that listens to Transaction creation/updates!
        # Let's check models.py signal `update_wallet_and_check_activation`.
        # If the transaction was created as 'debit', the wallet signal would have deducted the amount!
        
        # Wait, the buggy signals.py code was:
        # wallet.current_balance += amount  (Manual Credit) + wallet.save()
        # Transaction.objects.create(..., direction='debit') -> triggers signal
        # Signal says: if direction == 'debit': wallet.current_balance -= amount + wallet.save()
        # This means the manual credit was immediately canceled out by the signal debit!
        # Net effect on wallet balance: 0.
        
        # Now, if we just update the transaction to 'credit', the signal 'update_wallet_and_check_activation' 
        # only runs on POST_SAVE for created=True. 
        # Since we are updating an existing transaction (created=False), the signal will NOT run again automatically.
        # This is good because we can manually apply the correct credit to the wallet now.
        
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.current_balance += amount
        wallet.save(update_fields=['current_balance'])
        
        count += 1
        total_amount_corrected += amount
        print(f"Corrected {amount} for user {user.username} (Txn ID: {txn.id})")
        
    print(f"\nCorrection complete.")
    print(f"Total transactions corrected: {count}")
    print(f"Total amount credited back to wallets: Rs {total_amount_corrected}")

if __name__ == '__main__':
    main()
