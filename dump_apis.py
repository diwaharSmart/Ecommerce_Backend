import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

def dump_api(name, filename):
    try:
        api = Api.objects.get(name=name)
        with open(filename, "w") as f:
            f.write(api.content)
        print(f"Dumped {name} to {filename}")
    except Api.DoesNotExist:
        print(f"API {name} not found")

if __name__ == '__main__':
    dump_api("Get MLM Dashboard", "d:\\Ecommerce_Backend\\get_mlm_dashboard_api.py")
    dump_api("Get Profile", "d:\\Ecommerce_Backend\\get_profile_api.py")
