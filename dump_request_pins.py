import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

def dump_api():
    try:
        api = Api.objects.get(name="Request Pins")
        with open("d:\\Ecommerce_Backend\\request_pins_api.py", "w") as f:
            f.write(api.content)
        print("Successfully saved to request_pins_api.py")
    except Api.DoesNotExist:
        print("API not found")
        
if __name__ == '__main__':
    dump_api()
