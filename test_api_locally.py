import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_api():
    print("Testing /web/api/ authenticated as root...")
    client = Client()
    
    try:
        user = User.objects.get(username='root')
        # Simulate passing the valid auth token for 'root'
        client.force_login(user)
        
        payload = {
            'api_key': '91b1f76e-f709-499f-9e78-831ec42581e5',
            'username': 'root' # Pass the requested username
        }
        
        response = client.post('/web/api/', payload, content_type='application/json')
        print(f"Status Code: {response.status_code}")
        
        try:
             # Parse and format the output beautifully
             data = response.json()
             print(json.dumps(data, indent=4))
        except:
             print("Raw Response:", response.content)
             
    except Exception as e:
        print("Error during test:", str(e))

if __name__ == '__main__':
    test_api()
