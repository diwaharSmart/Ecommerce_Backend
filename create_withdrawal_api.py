
import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("Creating Withdrawal Request API...")

withdrawal_content = """
from ecommerce_app.models import WithdrawalRequest, Wallet, KYC
from decimal import Decimal

if request.user.is_authenticated:
    amount = request.data.get('amount')
    
    if amount:
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                 response_data['status_code'] = 400
                 response_data['message'] = "Amount must be positive"
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
                        
                        # Consider pending withdrawals? 
                        # Logic requested: "wallet has enough fund or not".
                        # Ideally: available = balance - pending_withdrawals
                        # Let's check pending first to be safer, if possible.
                        # pending_withdrawals = WithdrawalRequest.objects.filter(user=request.user, status='pending').aggregate(sum=Sum('amount'))['sum'] or 0
                        
                        if wallet.current_balance >= amount_decimal:
                             # Create Request
                             withdrawal = WithdrawalRequest.objects.create(
                                 user=request.user,
                                 amount=amount_decimal,
                                 status='pending'
                             )
                             response_data['status_code'] = 201
                             response_data['message'] = "Withdrawal request submitted successfully"
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

key_withdrawal = str(uuid.uuid4())
Api.objects.create(
    key=key_withdrawal,
    name="Request Withdrawal",
    method="POST",
    content=withdrawal_content,
    version=1.0
)
print(f"Created 'Request Withdrawal' API: {key_withdrawal}")
