
import os
import django
from django.core.files import File
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Category, Product

def create_grocery_data():
    # 1. Create Category
    category_name = "Grocery"
    category_slug = "grocery"
    
    category, created = Category.objects.get_or_create(
        slug=category_slug,
        defaults={
            'name': category_name,
            'description': 'Essential grocery items and packages.'
        }
    )
    
    if created:
        print(f"Created new category: {category.name}")
    else:
        print(f"Category already exists: {category.name}")

    # 2. Create Product
    product_name = "Grocery Package"
    product_slug = "grocery-package"
    product_price = 3000.00
    product_pv = 50
    
    # Path to the generated image (User will need to confirm the exact path/filename if slightly different)
    # Asking the agent system to use the artifact path logic is complex, relying on standard lookup
    # I'll look for the file in the artifacts folder relative to the script execution if possible, 
    # but for now I'll assume I can pass the path or just create the object and user uploads image manually if this fails.
    # HOWEVER, the prompt implies I should do it all.
    # I will assume the image is saved to the artifacts folder. 
    # I'll need to copy it to media/products/ first or open it directly.
    
    # Check if product exists
    product, created = Product.objects.get_or_create(
        slug=product_slug,
        defaults={
            'name': product_name,
            'category': category,
            'description': 'A comprehensive package of daily essential groceries including rice, oil, pulses, and spices.',
            'price': product_price,
            'stock': 100,
            'pv': product_pv,
            'is_active': True
        }
    )
    
    if created:
        print(f"Created new product: {product.name} with Price: {product.price} and PV: {product.pv}")
    else:
        print(f"Product already exists: {product.name}. Updating Price and PV.")
        product.price = product_price
        product.pv = product_pv
        product.category = category
        product.save()
        print(f"Updated product: {product.name}")

    # Handle Image
    # I will be notified of the image path in the next turn, so I will add a placeholder comment here
    # or better, I will run a separate snippet to attach the image once I know its filename.
    
    print("Done.")

if __name__ == "__main__":
    create_grocery_data()
