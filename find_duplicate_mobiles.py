import os
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User
from ecommerce_app.models import KYC, Wallet, Transaction
from django.db.models import Sum

def extract_mobile(user):
    username = user.username.lower()
    email = user.email.lower()
    
    if '@' in username:
        username_part = username.split('@')[0]
    else:
        username_part = username
        
    if '@' in email:
        email_part = email.split('@')[0]
    else:
        email_part = email
        
    if username_part.isdigit() and len(username_part) >= 5:
        return username_part
    if email_part.isdigit() and len(email_part) >= 5:
        return email_part
        
    return username_part

def find_duplicates():
    users = User.objects.all().prefetch_related('kyc')
    print(f"Total Users: {users.count()}")
    
    mobile_groups = {}
    
    for user in users:
        mobile = extract_mobile(user)
        if user.is_superuser or user.username == 'admin' or len(mobile) < 5:
            continue
            
        if mobile not in mobile_groups:
            mobile_groups[mobile] = []
        mobile_groups[mobile].append(user)
        
    all_groups = mobile_groups
    
    print(f"Generating report for {len(all_groups)} unique mobile numbers.")
    
    report_lines = []
    report_lines.append("="*80)
    report_lines.append(f"{'ALL ACCOUNTS REPORT (GROUPED BY MOBILE)' :^80}")
    report_lines.append("="*80)
    
    for phone, group in all_groups.items():
        # --- 1. Find Best KYC among the group ---
        shared_bank_acc = "N/A"
        shared_bank_name = "N/A"
        shared_ifsc = "N/A"
        shared_passbook_url = "N/A"
        
        for u in group:
            try:
                if hasattr(u, 'kyc'):
                    kyc = u.kyc
                    if kyc.bank_account_number and kyc.bank_account_number.strip():
                        shared_bank_acc = kyc.bank_account_number
                        shared_bank_name = kyc.bank_name
                        shared_ifsc = kyc.ifsc_code
                        if kyc.passbook_image:
                            try:
                                shared_passbook_url = kyc.passbook_image.url
                            except ValueError:
                                pass
                        break # Found one completely filled KYC
            except Exception:
                pass
                
        # --- 2. Print User Data ---
        report_lines.append(f"\n[ MOBILE NUMBER ]: {phone} (Accounts: {len(group)}, Sharing KYC: {'YES' if shared_bank_acc != 'N/A' else 'NO'})")
        report_lines.append("-" * 75)
        
        total_group_balance = 0.0
        
        for user in group:
            wallet, _ = Wallet.objects.get_or_create(user=user)
            current_bal = float(wallet.current_balance)
            total_group_balance += current_bal
            
            binary_inc = Transaction.objects.filter(
                user=user, type='binary_income', direction='credit'
            ).aggregate(Sum('amount'))['amount__sum'] or 0.0
            
            level_inc = Transaction.objects.filter(
                user=user, type='level_income', direction='credit'
            ).aggregate(Sum('amount'))['amount__sum'] or 0.0
            
            name = f"{user.first_name} {user.last_name}".strip() or "N/A"
            
            report_lines.append(f"  * Name      : {name}")
            report_lines.append(f"  * Username  : {user.username} (Email: {user.email})")
            report_lines.append(f"  * Mobile No : {phone}")
            report_lines.append(f"  * Bank Name : {shared_bank_name}")
            report_lines.append(f"  * Account No: {shared_bank_acc}")
            report_lines.append(f"  * IFSC Code : {shared_ifsc}")
            report_lines.append(f"  * Image URL : {shared_passbook_url}")
            report_lines.append(f"  * Wallet Bal: Rs {current_bal:.2f}")
            report_lines.append(f"  * Binary Inc: Rs {float(binary_inc):.2f}")
            report_lines.append(f"  * Level Inc : Rs {float(level_inc):.2f}")
            report_lines.append("  " + "." * 60)
            
        # --- 3. Grand Total for Duplicate Groups ---
        if len(group) > 1:
            report_lines.append(f"  ====> TOTAL GROUP WALLET BALANCE: Rs {total_group_balance:.2f} <====")
            
    filepath = "all_accounts_report_by_mobile.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Report completely saved to {filepath}")

if __name__ == '__main__':
    find_duplicates()
