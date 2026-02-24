import os
import django
from django.test import Client
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

def main():
    client = Client()
    
    # Try to find a specific user or any normal user
    user = User.objects.filter(is_superuser=False, username='D16641').first()
    if not user:
        user = User.objects.filter(is_superuser=False).first()
        
    if not user:
        print("No regular users found in the database. Cannot test authenticated APIs.")
        return
        
    print(f"Testing with User: {user.username}")
    token, _ = Token.objects.get_or_create(user=user)
    headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}
    
    apis_to_test = [
        'Get MLM Dashboard V2',
        'Get Profile',
        'Get Binary Tree',
        'Get Downline List'
    ]
    
    for api_name in apis_to_test:
        print(f"\n--- Testing API: {api_name} ---")
        api = Api.objects.filter(name=api_name).first()
        if not api:
            print(f"WARNING: API '{api_name}' not found in the database.")
            continue
            
        print(f"URL: /api/dynamic/{api.key}/")
        
        if api.method.upper() == 'POST':
            response = client.post(f'/api/dynamic/{api.key}/', **headers, content_type='application/json')
        elif api.method.upper() == 'GET':
            response = client.get(f'/api/dynamic/{api.key}/', **headers)
            
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response snippet: {json.dumps(data, indent=2)[:300]}...")
            except:
                print(f"Response snippet: {str(response.content)[:300]}...")
        else:
            print(f"Error Response: {response.content}")

if __name__ == '__main__':
    main()
