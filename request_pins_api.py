from ecommerce_app.models import PinRequest,Transaction,Pin
import uuid
if request.user.is_authenticated:
    number_of_pins = request.data.get('number_of_pins')
    if int(request.user.wallet.current_balance)>=number_of_pins:
        for _ in range(int(number_of_pins)):
            while True:
                code = str(uuid.uuid4()).replace('-', '')[:10].upper()
                if not Pin.objects.filter(code=code).exists():
                    break
            
            if int(request.user.wallet.current_balance)>=number_of_pins:
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
                    description=f"Pin Purchase",
                    # related_withdrawal=instance
                )

    else:
        response_data['status_code'] = 400
        response_data['message'] = "number_of_pins required"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"