import os
import django

# 1. First set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')

# 2. Then call django.setup()
django.setup()

# 3. ONLY THEN import models and signals
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from ecommerce_app.models import (
    create_user_profile, 
    save_user_profile, 
    create_user_wallet,
    approve_payin_request,
    update_wallet_and_check_activation,
    process_withdrawal_status_change,
    generate_coupons_on_order_paid,
    Profile, Wallet, Category, Product, Order, OrderItem, 
    KYC, Pin, PinRequest, WithdrawalRequest, Transaction,
    PayinRequest
)
from ecommerce_app.signals import (
    order_post_save,
    generate_pins_on_approval
)
from website.models import Api, JsonSerializer

def clear_db():
    print("Clearing database...")
    Transaction.objects.all().delete()
    WithdrawalRequest.objects.all().delete()
    PinRequest.objects.all().delete()
    Pin.objects.all().delete()
    KYC.objects.all().delete()
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Wallet.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.all().delete()
    ContentType.objects.all().delete()
    Api.objects.all().delete()
    JsonSerializer.objects.all().delete()
    PayinRequest.objects.all().delete()
    print("Database cleared!")

def run_loaddata():
    clear_db()
    
    # 1. Disconnect signals
    print("Disconnecting all signals...")
    # From models.py
    post_save.disconnect(create_user_profile, sender=User)
    post_save.disconnect(save_user_profile, sender=User)
    post_save.disconnect(create_user_wallet, sender=User)
    post_save.disconnect(approve_payin_request, sender=PayinRequest)
    post_save.disconnect(update_wallet_and_check_activation, sender=Transaction)
    post_save.disconnect(process_withdrawal_status_change, sender=WithdrawalRequest)
    post_save.disconnect(generate_coupons_on_order_paid, sender=Order)
    
    # From signals.py
    post_save.disconnect(order_post_save, sender=Order)
    post_save.disconnect(generate_pins_on_approval, sender=PinRequest)

    # 2. Run loaddata
    print("Running loaddata (excluding system apps)...")
    try:
        # Exclude contenttypes, permissions, and admin logs to avoid ID conflicts
        call_command(
            'loaddata', 
            'datadump_utf8.json', 
            verbosity=2, 
            exclude=['contenttypes', 'auth.Permission', 'admin.LogEntry']
        )
        print("Loaddata finished successfully!")
    except Exception as e:
        print(f"Loaddata failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # No need to reconnect since the script ends here
        print("Done.")

if __name__ == '__main__':
    run_loaddata()
