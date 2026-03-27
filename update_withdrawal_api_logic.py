import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

def main():
    print("Updating 'Request Withdrawal' API with 80/10/10 split logic...")
    api = Api.objects.filter(name="Request Withdrawal").first()
    if not api:
        print("Error: 'Request Withdrawal' API not found!")
        return

    withdrawal_content = """from ecommerce_app.models import WithdrawalRequest, Wallet, KYC
from decimal import Decimal

if request.user.is_authenticated:
    amount = request.data.get('amount')
    
    if amount:
        try:
            total_decimal = Decimal(str(amount))
            if total_decimal < 500:
                 response_data['status_code'] = 400
                 response_data['message'] = "Minimum withdrawal amount is Rs 500"
            else:
                # 1. Check KYC Status
                try:
                    kyc = KYC.objects.get(user=request.user)
                    if kyc.status != 'verified':
                        response_data['status_code'] = 400
                        response_data['message'] = "KYC not verified. Please complete KYC checks."
                    else:
                        # 2. Check Wallet Balance
                        wallet, _ = Wallet.objects.get_or_create(user=request.user)
                        
                        if wallet.current_balance >= total_decimal:
                             # Calculate Split
                             tds = total_decimal * Decimal("0.10")
                             top_up = total_decimal * Decimal("0.10")
                             net = total_decimal - tds - top_up
                             
                             # Create Request (Signals handle the wallet movement)
                             withdrawal = WithdrawalRequest.objects.create(
                                 user=request.user,
                                 total_amount=total_decimal,
                                 amount=net, # Net Amount (80%)
                                 tds_amount=tds,
                                 top_up_amount=top_up,
                                 status='pending'
                             )
                             response_data['status_code'] = 201
                             response_data['message'] = "Withdrawal request submitted. Rs {0} deducted (Net: {1}, TDS: {2}, TopUp: {3})".format(total_decimal, net, tds, top_up)
                             response_data['request_id'] = withdrawal.id
                        else:
                             response_data['status_code'] = 400
                             response_data['message'] = "Insufficient Wallet Balance"
                             
                except KYC.DoesNotExist:
                     response_data['status_code'] = 400
                     response_data['message'] = "KYC not found. Please submit KYC."
                
        except Exception as e:
             response_data['status_code'] = 500
             response_data['message'] = str(e)
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Amount required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""
    api.content = withdrawal_content
    api.version = float(api.version) + 0.1
    api.save()
    print(f"Successfully updated 'Request Withdrawal' API to version {api.version}")

if __name__ == '__main__':
    main()
