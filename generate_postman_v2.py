
import os
import django
import json
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

BASE_URL = "http://127.0.0.1:8000/web/api/"
COLLECTION_NAME = "Django MLM Ecommerce V2"

# Defined sample bodies for known APIs to ensure quality
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
        "action": "add",
        "address_line1": "123 Main St",
        "city": "Metropolis",
        "state": "NY",
        "pincode": "10001",
        "phone": "9876543210"
    },
    "Manage KYC": {
        "action": "create",
        "name_on_card": "John Doe",
        "aadhar_number": "123456789012",
        "pan_number": "ABCDE1234F",
        "bank_name": "State Bank of India",
        "bank_account_number": "1234567890",
        "ifsc_code": "SBIN0001234",
        "account_holder_name": "John Doe"
        # Images handled separately in Postman (form-data), but here we document JSON structure or similar
    },
    "Request Pins": {
        "number_of_pins": 5
    },
    "Get Pins": {
        "status": "active" # optional
    },
    "Redeem Pin": {
        "pin_id": 1,
        "username": "TargetUser",
        "product_id": 1
    },
    "Create Ticket": {
        "subject": "Payment Issue",
        "message": "I made a payment but wallet not updated."
    },
    "Get Binary Tree": {
        "user_id": 1 # optional
    },
    "Get Level Members": {
        "user_id": 1 # optional
    },
    "Request Withdrawal": {
        "amount": 1000.00
    },
    "Redeem Coupon": {
        "coupon_id": 1
    },
    "Get Downline List": {
        "user_id": 1 # optional
    },
    "Edit Profile Picture": {
        "__mode__": "formdata",
        "profile_image": "file" # Special marker
    },
    "Get Category Products": {}, # GET request usually, but here dynamic POST
    "Get MLM Dashboard": {}, 
    "Get Wallet": {},
    "Home Data": {},
    "Get Cart": {},
    "Remove from Cart": {"product_id": 1},
    "Checkout": {"address_id": 1, "payment_mode": "cod"},
    "Get Tickets": {},
    "Get Coupons": {}
}

SAMPLE_RESPONSES = {
    "Login User": {
        "status_code": 200,
        "message": "Login successful",
        "token": "fd9d9...",
        "user_id": 1,
        "username": "VEDAON_1234567"
    },
    "Get MLM Dashboard": {
        "status_code": 200,
        "data": {
            "user_info": {"username": "VEDAON_1234567", "first_name": "John"},
            "overall_income": {"total_credit": 5000.0, "binary_income_sum": 2000.0},
            "team_stats": {"total_left_count": 10, "total_right_count": 15},
            "recent_orders": []
        }
    },
    # Add generic success for others
    "DEFAULT": {
        "status_code": 200,
        "message": "Success",
        "data": {}
    }
}

collection = {
    "info": {
        "name": COLLECTION_NAME,
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": []
}

apis = Api.objects.all().order_by('name')

print(f"Found {apis.count()} APIs. Generating collection...")

for api in apis:
    name = api.name
    key = api.key
    method = api.method
    
    # payload
    raw_body = ""
    mode = "raw"
    options = {"raw": {"language": "json"}}
    
    if name in SAMPLE_PAYLOADS:
        raw_body = json.dumps(SAMPLE_PAYLOADS[name], indent=4)
        
    request_item = {
        "name": name,
        "request": {
            "method": method,
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json",
                    "type": "text"
                },
                {
                    "key": "x-api-key",
                    "value": key,
                    "type": "text",
                    "description": "Dynamic API Key"
                },
                {
                    "key": "Authorization",
                    "value": "Token <YOUR_AUTH_TOKEN>",
                    "type": "text",
                    "description": "Replace with login token"
                }
            ],
            "url": {
                "raw": BASE_URL,
                "protocol": "http",
                "host": ["127", "0", "0", "1"],
                "port": "8000",
                "path": ["web", "api", ""]
            }
        }
    }

    if method == "POST":
         # Check for special mode in SAMPLE_PAYLOADS
         is_formdata = False
         if name in SAMPLE_PAYLOADS and "__mode__" in SAMPLE_PAYLOADS[name] and SAMPLE_PAYLOADS[name]["__mode__"] == "formdata":
             is_formdata = True
             
         if is_formdata:
             formdata_items = []
             for k, v in SAMPLE_PAYLOADS[name].items():
                 if k == "__mode__":
                     continue
                 item = {"key": k, "type": "text", "value": str(v)}
                 if v == "file":
                     item = {"key": k, "type": "file", "src": []}
                 formdata_items.append(item)
                 
             request_item["request"]["body"] = {
                 "mode": "formdata",
                 "formdata": formdata_items
             }
             # Remove Content-Type header if present, as Postman/Browser sets it for multipart
             request_item["request"]["header"] = [h for h in request_item["request"]["header"] if h["key"] != "Content-Type"]
             
         else:
             # Default Raw JSON
             request_item["request"]["body"] = {
                 "mode": mode,
                 "raw": raw_body,
                 "options": options
             }
         
    # Add Sample Response
    sample_res_body = SAMPLE_RESPONSES.get(name, SAMPLE_RESPONSES["DEFAULT"])
    response_item = {
        "name": "Success Example",
        "originalRequest": request_item["request"],
        "status": "OK",
        "code": 200,
        "_postman_previewlanguage": "json",
        "header": [],
        "cookie": [],
        "body": json.dumps(sample_res_body, indent=4)
    }
    request_item["response"] = [response_item]

    # Add to collection
    collection["item"].append(request_item)

output_path = r"C:\Users\naaar\.gemini\antigravity\brain\fa6e70a0-9403-408a-80a6-4949d142db12\postman_collection_v2.json"
with open(output_path, "w") as f:
    json.dump(collection, f, indent=4)

print(f"Successfully generated Postman Collection at: {output_path}")
