
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

apis = Api.objects.all().order_by('name')


print("Writing keys to api_keys.txt...")
output_path = r"C:\Users\naaar\.gemini\antigravity\brain\fa6e70a0-9403-408a-80a6-4949d142db12\api_keys.txt"

with open(output_path, "w") as f:
    f.write("Django MLM Ecommerce - API Keys\n")
    f.write("==================================\n")
    f.write("Base URL: http://127.0.0.1:8000/web/api/\n\n")
    
    for api in apis:
        f.write(f"{api.name}: {api.key}\n")

print(f"Updated {output_path}")

