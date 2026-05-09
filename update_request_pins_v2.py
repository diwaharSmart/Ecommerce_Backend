import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

new_code = """
from ecommerce_app.models import PinRequest, Transaction, Pin
from django.db.models import Sum
from django.utils import timezone
import datetime
import uuid

if request.user.is_authenticated:
    number_of_pins = request.data.get('number_of_pins')
    if number_of_pins is None:
        response_data['status_code'] = 400
        response_data['message'] = "number_of_pins required"
    else:
        number_of_pins = int(number_of_pins)
        total_pin_cost = number_of_pins * 3000

        # Define the Cut-off Date (May 8, 2026) to forgive past negative balances
        cutoff_date = datetime.datetime(2026, 5, 8, tzinfo=timezone.utc)
        
        # 1. Past Balance (Before Cut-off)
        past_deposits = Transaction.objects.filter(
            user=request.user, type='deposit', direction='credit', created_at__lt=cutoff_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        past_purchases = Transaction.objects.filter(
            user=request.user, type__in=['pin_purchase', 'purchase'], direction='debit', created_at__lt=cutoff_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Floor negative past balances to 0
        past_balance = max(0, past_deposits - past_purchases)
        
        # 2. New Balance (After Cut-off)
        new_deposits = Transaction.objects.filter(
            user=request.user, type='deposit', direction='credit', created_at__gte=cutoff_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        new_purchases = Transaction.objects.filter(
            user=request.user, type__in=['pin_purchase', 'purchase'], direction='debit', created_at__gte=cutoff_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        new_balance = new_deposits - new_purchases
        
        # 3. Final Available Deposit
        available_deposit_balance = past_balance + new_balance
        
        if available_deposit_balance >= total_pin_cost:
            for _ in range(number_of_pins):
                while True:
                    code = str(uuid.uuid4()).replace('-', '')[:10].upper()
                    if not Pin.objects.filter(code=code).exists():
                        break
                
                Pin.objects.create(
                    owner=request.user,
                    code=code,
                    value=3000.00,
                    status='active'
                )
                Transaction.objects.create(
                    user=request.user,
                    amount=3000,
                    direction='debit',
                    type='pin_purchase',
                    description="Pin Purchase"
                )
            
            response_data['status_code'] = 200
            response_data['message'] = f"Successfully purchased {number_of_pins} pins."
        else:
            response_data['status_code'] = 400
            response_data['message'] = f"Insufficient deposit balance. Available: {available_deposit_balance}, Required: {total_pin_cost}"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

def update_api():
    try:
        api = Api.objects.get(name="Request Pins")
        api.content = new_code.strip()
        api.version = float(api.version) + 0.1
        api.save()
        print("Successfully updated 'Request Pins' API with Option 1 Cut-off logic.")
    except Api.DoesNotExist:
        print("API not found")

if __name__ == '__main__':
    update_api()
