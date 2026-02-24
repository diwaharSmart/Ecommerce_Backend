
import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

# Define Sample Payloads (Shared source of truth)
SAMPLE_PAYLOADS = {
    "Register User": {
        "name": "John Doe",
        "mobile": "john@example.com",
        "password": "securepassword",
        "sponsor_id": "1",
        "position": "L"
    },
    "Login User": {
        "username": "VEDAON_1234567",
        "password": "securepassword"
    },
    "Change Password": {
        "old_password": "securepassword",
        "new_password": "newpassword123"
    },
    "Create Payin": {
        "amount": 5000.00,
        "reference_number": "REF123456789"
    },
    "Add to Cart": {
        "product_id": 1,
        "quantity": 2
    },
    "Remove from Cart": {
        "product_id": 1
    },
    "Manage Address": {
        "action": "add/edit/delete/get",
        "address_line1": "123 Main St",
        "city": "Metropolis",
        "state": "NY",
        "pincode": "10001",
        "phone": "9876543210"
    },
    "Manage KYC": {
        "action": "create/edit/get",
        "name_on_card": "John Doe",
        "aadhar_number": "1234-5678-9012",
        "pan_number": "ABCDE1234F"
    },
    "Request Pins": {
        "number_of_pins": 5
    },
    "Get Pins": {
        "status": "active"
    },
    "Redeem Pin": {
        "pin_id": 1,
        "username": "TargetUser"
    },
    "Create Ticket": {
        "subject": "Payment Issue",
        "message": "Description..."
    },
    "Get Binary Tree": {
        "user_id": 1 
    },
    "Get Level Members": {
        "user_id": 1 
    },
    "Request Withdrawal": {
        "amount": 1000.00
    },
    "Redeem Coupon": {
        "coupon_id": 1
    },
     "Edit Profile Picture": {
        "profile_image": "(File Upload)"
    }
}

apis = Api.objects.all().order_by('name')

OUTPUT_PATH = r"C:\Users\naaar\.gemini\antigravity\brain\fa6e70a0-9403-408a-80a6-4949d142db12\API_DOCUMENTATION.md"

with open(OUTPUT_PATH, "w") as f:
    f.write("# API Documentation\n\n")
    f.write("Base URL: `http://127.0.0.1:8000/web/api/`\n\n")
    f.write("> **Authentication**: Most APIs require `Authorization: Token <token>` header.\n")
    f.write("> **API Key**: All APIs require `x-api-key: <UUID>` header.\n\n")
    f.write("---\n\n")
    
    for api in apis:
        f.write(f"## {api.name}\n\n")
        f.write(f"**Method**: `{api.method}`\n\n")
        f.write(f"**Key**: `{api.key}`\n\n")
        
        # Add payload if available
        if api.name in SAMPLE_PAYLOADS:
            payload = json.dumps(SAMPLE_PAYLOADS[api.name], indent=4)
            f.write("**Request Body**:\n")
            f.write("```json\n")
            f.write(payload + "\n")
            f.write("```\n\n")
        else:
             if api.method == "POST":
                 f.write("**Request Body**: (Check usage details)\n\n")
        
        f.write("---\n\n")

print(f"Generated documentation for {apis.count()} APIs at {OUTPUT_PATH}")
