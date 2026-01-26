import os
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Category, Product, Banner

def populate():
    print("Populating static data...")

    # --- Banners ---
    print("Creating Banners...")
    banners = [
        {
            "title": "Big Sale 50% Off",
            "image": "banners/banner_sale.png",
            "link": "/sale",
            "active": True
        },
        {
            "title": "New Arrivals",
            "image": "banners/banner_new_arrival.png",
            "link": "/new-arrivals",
            "active": True
        },
        {
            "title": "Best Electronics",
            "image": "banners/banner_electronics.png",
            "link": "/electronics",
            "active": True
        }
    ]

    for b in banners:
        Banner.objects.get_or_create(
            title=b['title'],
            defaults={
                "image": b['image'],
                "link": b['link'],
                "is_active": b['active'],
                "from_date": timezone.now(),
                "to_date": timezone.now() + timedelta(days=365)
            }
        )

    # --- Categories ---
    print("Creating Categories...")
    categories = [
        "Electronics",
        "Grocery",
        "Fashion",
        "Home & Furniture"
    ]
    
    cat_objs = {}
    for cat_name in categories:
        cat, created = Category.objects.get_or_create(name=cat_name)
        cat_objs[cat_name] = cat

    # --- Products ---
    print("Creating Products...")
    products = [
        # Electronics
        {
            "name": "Smartphone X Pro",
            "category": "Electronics",
            "price": 25000.00,
            "pv": 100,
            "description": "Latest smartphone with high-end features."
        },
        {
            "name": "Wireless Headphones",
            "category": "Electronics",
            "price": 5000.00,
            "pv": 20,
            "description": "Noise cancelling wireless headphones."
        },
        {
            "name": "4K Smart TV",
            "category": "Electronics",
            "price": 45000.00,
            "pv": 200,
            "description": "55 inch 4K Ultra HD Smart LED TV."
        },
        # Grocery
        {
            "name": "Premium Basmati Rice (5kg)",
            "category": "Grocery",
            "price": 800.00,
            "pv": 5,
            "description": "Long grain aromatic basmati rice."
        },
        {
            "name": "Organic Almonds (500g)",
            "category": "Grocery",
            "price": 600.00,
            "pv": 4,
            "description": "High quality organic almonds."
        },
        # Fashion
        {
            "name": "Men's Casual Shirt",
            "category": "Fashion",
            "price": 1200.00,
            "pv": 8,
            "description": "Comfortable cotton casual shirt."
        },
        {
            "name": "Women's Stylish Dress",
            "category": "Fashion",
            "price": 2500.00,
            "pv": 15,
            "description": "Elegant evening wear dress."
        }
    ]

    for p in products:
        Product.objects.get_or_create(
            name=p['name'],
            defaults={
                "category": cat_objs[p['category']],
                "price": p['price'],
                "pv": p['pv'],
                "description": p['description'],
                "stock": 100,
                "available": True
            }
        )

    print("Data population complete!")

if __name__ == '__main__':
    populate()
