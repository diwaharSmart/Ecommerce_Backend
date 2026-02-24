import os
import sys
import django
from django.core.files import File

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Category, Product, Profile, PayinRequest, KYC, Banner

def migrate_field(instance, field_name):
    field = getattr(instance, field_name)
    if not field or not field.name:
        return

    # Skip if field is already a Cloudinary URL (e.g. starts with 'http' or 'cloudinary')
    if field.name.startswith('http') or field.name.startswith('cloudinary'):
        return

    # Path to local file
    from django.conf import settings
    local_path = os.path.join(settings.BASE_DIR, 'media', field.name)
    
    if os.path.exists(local_path):
        print(f"Uploading {local_path} to Cloudinary...")
        with open(local_path, 'rb') as f:
            # We assign to the field, calling save will trigger Cloudinary storage
            # We use the existing filename
            django_file = File(f, name=os.path.basename(field.name))
            setattr(instance, field_name, django_file)
            instance.save(update_fields=[field_name])
        print(f"Success! New path: {getattr(instance, field_name).url}")
    else:
        print(f"Warning: File {local_path} not found locally.")

def main():
    if 'CLOUDINARY_URL' not in os.environ:
        print("ERROR: CLOUDINARY_URL environment variable is not set.")
        print("Please set it before running this script.")
        print("Example: set CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>")
        sys.exit(1)
        
    print("Starting Cloudinary media migration...")
    
    models_to_check = [
        (Category, ['image']),
        (Product, ['image']),
        (Profile, ['profile_image']),
        (PayinRequest, ['screenshot']),
        (KYC, ['aadhar_image', 'pan_image', 'passbook_image']),
        (Banner, ['image']),
    ]
    
    for model, fields in models_to_check:
        instances = model.objects.all()
        for instance in instances:
            for field in fields:
                migrate_field(instance, field)
                
    print("Migration complete!")

if __name__ == '__main__':
    main()
