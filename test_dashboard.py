import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient

def check_dashboard():
    print("Testing /api/dashboard/ for user: root")
    client = APIClient()
    try:
        user = User.objects.get(username='root')
        client.force_authenticate(user=user)
        
        response = client.post('/api/get-dashboard-data/', {'username': 'root'}, format='json')
        print(f"Status Code: {response.status_code}")
        try:
             print(json.dumps(response.json(), indent=4))
        except:
             print(response.content)
             
    except User.DoesNotExist:
        print("Root user not found for testing.")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    check_dashboard()
