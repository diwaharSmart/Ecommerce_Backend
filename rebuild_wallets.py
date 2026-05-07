import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import User, Wallet, Transaction
from django.db import transaction as db_transaction
from django.db.models import Sum

def rebuild_wallets():
    print("Starting exact wallet rebuild from transaction history (Optimized)...")
    
    # 1. Update binary income type natively
    updated = Transaction.objects.filter(type='binary_income').exclude(direction='credit').update(direction='credit')
    print(f"Standardized {updated} binary_income transactions.")

    # 2. Get all Wallet instances
    wallets = {w.user_id: w for w in Wallet.objects.all()}
    
    # Track top up balances
    tu_credits = Transaction.objects.filter(type='top_up', direction='credit').values('user_id').annotate(total=Sum('amount'))
    tu_debits = Transaction.objects.filter(type='top_up', direction='debit').values('user_id').annotate(total=Sum('amount'))
    
    # Track current main balance
    cb_credits = Transaction.objects.exclude(type='top_up').filter(direction='credit').values('user_id').annotate(total=Sum('amount'))
    cb_debits = Transaction.objects.exclude(type='top_up').filter(direction='debit').values('user_id').annotate(total=Sum('amount'))

    # Helper maps
    def to_map(qs):
        return {item['user_id']: item['total'] or Decimal("0.00") for item in qs}
        
    tu_c_map = to_map(tu_credits)
    tu_d_map = to_map(tu_debits)
    cb_c_map = to_map(cb_credits)
    cb_d_map = to_map(cb_debits)

    users = User.objects.all()
    wallets_to_update = []
    
    for u in users:
        uid = u.id
        if uid not in wallets:
            w = Wallet(user=u)
            w.save()
            wallets[uid] = w
            
        wallet = wallets[uid]
        c_tu = tu_c_map.get(uid, Decimal("0.00"))
        d_tu = tu_d_map.get(uid, Decimal("0.00"))
        c_cb = cb_c_map.get(uid, Decimal("0.00"))
        d_cb = cb_d_map.get(uid, Decimal("0.00"))
        
        wallet.top_up_balance = Decimal(str(c_tu)) - Decimal(str(d_tu))
        wallet.current_balance = Decimal(str(c_cb)) - Decimal(str(d_cb))
        wallets_to_update.append(wallet)

    Wallet.objects.bulk_update(wallets_to_update, ['top_up_balance', 'current_balance'])
    print(f"Successfully calculated and bulk-rebuilt exact balances for {len(wallets_to_update)} wallets!")

if __name__ == '__main__':
    rebuild_wallets()
