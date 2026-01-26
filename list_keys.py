import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

print("List of APIs in DB:")
for api in Api.objects.all():
    print(f"Name: {api.name}, Key: {api.key}")
