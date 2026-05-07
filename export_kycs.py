import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import KYC, Wallet, Transaction
from django.db.models import Sum

def export_kyc_data():
    verified_kycs = KYC.objects.filter(status='verified').select_related('user')
    print(f"Found {verified_kycs.count()} verified KYCs.")
    
    report_lines = []
    report_lines.append("="*80)
    report_lines.append(f"{'VERIFIED KYC USERS AND WALLET REPORT':^80}")
    report_lines.append("="*80)
    
    for idx, kyc in enumerate(verified_kycs, 1):
        user = kyc.user
        
        # KYC Details
        bank_acc = kyc.bank_account_number
        bank_name = kyc.bank_name
        ifsc = kyc.ifsc_code
        try:
            image_url = kyc.passbook_image.url if kyc.passbook_image else "No Image"
        except ValueError: # The attribute has no file associated with it.
            image_url = "No Image"
            
        # Wallet Balance
        wallet, _ = Wallet.objects.get_or_create(user=user)
        current_balance = wallet.current_balance
        
        # Payout Details
        binary_income = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        level_income = Transaction.objects.filter(
            user=user, type='level_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        
        report_lines.append(f"User {idx}: {user.username} (Name: {user.first_name} {user.last_name})")
        report_lines.append(f"  - Bank Name       : {bank_name}")
        report_lines.append(f"  - Acc Number      : {bank_acc}")
        report_lines.append(f"  - IFSC Code       : {ifsc}")
        report_lines.append(f"  - Passbook URL    : {image_url}")
        report_lines.append(f"  - Binary Income   : Rs {float(binary_income)}")
        report_lines.append(f"  - Level Income    : Rs {float(level_income)}")
        report_lines.append(f"  - Current Balance : Rs {float(current_balance)}")
        report_lines.append("-" * 80)
        
    filepath = "verified_kyc_report.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Successfully generated report at {filepath}")

if __name__ == '__main__':
    export_kyc_data()
