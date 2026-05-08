import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

new_code = """
from ecommerce_app.models import PinRequest, Transaction, Pin
from django.db.models import Sum
import uuid

if request.user.is_authenticated:
    number_of_pins = request.data.get('number_of_pins')
    if number_of_pins is None:
        response_data['status_code'] = 400
        response_data['message'] = "number_of_pins required"
    else:
        number_of_pins = int(number_of_pins)
        total_pin_cost = number_of_pins * 3000

        # Calculate available deposit balance
        total_deposits = Transaction.objects.filter(
            user=request.user, 
            type='deposit', 
            direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        total_purchases = Transaction.objects.filter(
            user=request.user, 
            type__in=['pin_purchase', 'purchase'], 
            direction='debit'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        available_deposit_balance = total_deposits - total_purchases
        
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
        print("Successfully updated 'Request Pins' API in database")
    except Api.DoesNotExist:
        print("API not found")

if __name__ == '__main__':
    update_api()
