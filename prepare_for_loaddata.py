import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from ecommerce_app.models import Profile, Wallet, Category, Product, Order, OrderItem, KYC, Pin, PinRequest, WithdrawalRequest, Transaction
from website.models import Api, JsonSerializer

def clear_db():
    print("Clearing database...")
    # Order matters due to foreign keys
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
    ContentType.objects.all().delete() # Important
    Api.objects.all().delete()
    JsonSerializer.objects.all().delete()
    print("Database cleared!")

if __name__ == '__main__':
    clear_db()
