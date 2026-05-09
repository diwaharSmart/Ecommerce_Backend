import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Product, Order, OrderItem, Transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
import datetime

today = timezone.now()
start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
start_of_week = today - datetime.timedelta(days=today.weekday())
start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

# Calculate Valid Turnover (Purchases excluding 1 PV products)
# Using OrderItem to sum (quantity * price) for products where PV > 1
# Assuming 'status="paid"' is used to mark completed purchases.
valid_order_items = OrderItem.objects.filter(order__status='paid', product__pv__gt=1, order__created_at__gte=start_of_today)
today_valid_purchase = valid_order_items.annotate(
    total_cost=ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())
).aggregate(Sum('total_cost'))['total_cost__sum'] or 0

# Also include pin_purchases? A pin purchase is 3000. Does a pin have PV? 
today_pin_purchases = Transaction.objects.filter(type='pin_purchase', direction='debit', created_at__gte=start_of_today).aggregate(Sum('amount'))['amount__sum'] or 0

today_total_purchase = today_valid_purchase + today_pin_purchases

print(f"Today Valid Purchase: {today_valid_purchase}")
print(f"Today Pin Purchase: {today_pin_purchases}")
print(f"Today Total Purchase (Turnover Base): {today_total_purchase}")

# Total 1 PV Products Activated (Quantity)
one_pv_items = OrderItem.objects.filter(order__status='paid', product__pv=1)
total_1pv_quantity = one_pv_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
print(f"Total 1 PV products activated: {total_1pv_quantity}")

