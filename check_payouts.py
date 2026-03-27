import os
import django
from django.db.models import Sum

os.environ['USE_UAT_DB'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Transaction, Profile, Order

binary_count = Transaction.objects.filter(type='binary_income').count()
binary_sum = Transaction.objects.filter(type='binary_income').aggregate(Sum('amount'))['amount__sum'] or 0

level_count = Transaction.objects.filter(type='level_income').count()
level_sum = Transaction.objects.filter(type='level_income').aggregate(Sum('amount'))['amount__sum'] or 0

total_revenue = Order.objects.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

print(f"Current Payout Metrics:")
print(f"-> Total Pair Matches: {binary_count} pairs (Distributed matching income Rs. {binary_sum})")
print(f"-> Level Matching Dist: {level_count} transactions (Distributed level income Rs. {level_sum})")
print(f"-> Total Users: {Profile.objects.count()}")

print(f"--------------------------------")
print(f"Total Revenue Generated: Rs. {total_revenue}")
profit = float(total_revenue) - float(binary_sum) - float(level_sum)
print(f"Final Company Profit (Revenue - Payouts): Rs. {profit}")
