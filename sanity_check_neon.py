import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User
from ecommerce_app.models import Profile, Wallet, Order

def sanity_check():
    user_count = User.objects.count()
    profile_count = Profile.objects.count()
    wallet_count = Wallet.objects.count()
    order_count = Order.objects.count()
    
    print(f"Sanity Check Results:")
    print(f"Total Users: {user_count}")
    print(f"Total Profiles: {profile_count}")
    print(f"Total Wallets: {wallet_count}")
    print(f"Total Orders: {order_count}")
    
    if user_count > 0:
        print("Migration looks successful!")
    else:
        print("Warning: Database seems empty.")

if __name__ == '__main__':
    sanity_check()
