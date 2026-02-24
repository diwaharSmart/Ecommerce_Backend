
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from website.models import Api

# Key from previous shell output
KYC_API_KEY = "cadcbdcb-77d3-4caa-bca0-02dce1b704da"

# New Content Definition (Using serializer is key, but I should ensure serializer has new fields)
# Since I use 'KB' style, the serializer handles the fields automatically if I add them to 'fields = "__all__"'
# which it is. BUT, I should ensure the 'create' action handles file uploads correctly if passed in request.data.
# The previous code: serializer = KYCSerializer(data=request.data) handles it.

kyc_content = """
from ecommerce_app.models import KYC
from ecommerce_app.serializers import KYCSerializer

if request.user.is_authenticated:
    action = request.data.get('action') # 'create', 'edit', 'get'
    
    if action == 'create':
        if KYC.objects.filter(user=request.user).exists():
             response_data['status_code'] = 400
             response_data['message'] = "KYC already exists"
        else:
            # Serializer handles file uploads if passed in request.FILES / request.data
            serializer = KYCSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                response_data['status_code'] = 201
                response_data['message'] = "KYC submitted"
                response_data['data'] = serializer.data
            else:
                response_data['status_code'] = 400
                response_data['message'] = str(serializer.errors)
                
    elif action == 'edit':
        try:
            kyc = KYC.objects.get(user=request.user)
            if kyc.status == 'verified':
                 response_data['status_code'] = 400
                 response_data['message'] = "Cannot edit verified KYC"
            else:
                # partial=True allows creating/updating with subset of fields
                serializer = KYCSerializer(kyc, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    response_data['status_code'] = 200
                    response_data['message'] = "KYC updated"
                    response_data['data'] = serializer.data
                else:
                    response_data['status_code'] = 400
                    response_data['message'] = str(serializer.errors)
        except KYC.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "KYC not found"

    elif action == 'get' or action is None:
        try:
            kyc = KYC.objects.get(user=request.user)
            serializer = KYCSerializer(kyc)
            response_data['status_code'] = 200
            response_data['data'] = serializer.data
            response_data['message'] = "KYC details fetched"
        except KYC.DoesNotExist:
             response_data['status_code'] = 404
             response_data['message'] = "KYC not found"
             
    else:
        response_data['status_code'] = 400
        response_data['message'] = "Invalid action"
else:
    response_data['status_code'] = 401
    response_data['message'] = "Unauthorized"
"""

try:
    api = Api.objects.get(key=KYC_API_KEY)
    api.content = kyc_content
    # api.version += 0.1 # Optional version bump
    api.save()
    print(f"Successfully updated API: {api.name} ({api.key})")
except Api.DoesNotExist:
    # Fallback to name search if key was wrong (unlikely given previous step)
    try:
        api = Api.objects.get(name="Manage KYC")
        print(f"Key mismatch? Found by name. Old Key: {api.key}")
        # api.key = KYC_API_KEY # Do not change key if found, unless necessary. User said "dont change uuid". 
        # Actually user said "dont change uuid" meaning keep the EXISTING one.
        # So I only update content.
        api.content = kyc_content
        api.save()
        print(f"Successfully updated API by Name: {api.name} ({api.key})")
    except Api.DoesNotExist:
        print("Error: KYC API not found.")

