import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Category, Product

print("--- Categories ---")
for c in Category.objects.all():
    print(f"ID: {c.id}, Name: {c.name}, Slug: {c.slug}")

print("\n--- Products ---")
for p in Product.objects.filter(name__icontains='Buckthorn'):
    print(f"ID: {p.id}, Name: {p.name}, Category: {p.category.name}, Price: {p.price}, PV: {p.pv}")

for p in Product.objects.filter(name__icontains='Grocery') | Product.objects.filter(category__name__icontains='grocery'):
    if p.pv == 50 or 'coupen' in p.name.lower() or 'package' in p.name.lower():
         print(f"ID: {p.id}, Name: {p.name}, Category: {p.category.name}, Price: {p.price}, PV: {p.pv}")
