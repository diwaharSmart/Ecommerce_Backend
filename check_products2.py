import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Product, Order, OrderItem

products = [(p.name, p.pv) for p in Product.objects.all()]
print("Products:", products)
