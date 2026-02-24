
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User

target_username = "VN2813230"
new_password = "04021977"

print(f"Attempting to change password for: {target_username}")

try:
    user = User.objects.get(username=target_username)
    user.set_password(new_password)
    user.save()
    print(f"SUCCESS: Password changed for user '{target_username}'")
except User.DoesNotExist:
    print(f"ERROR: User '{target_username}' not found.")
    
    # Suggest alternatives
    print("Checking for similar usernames...")
    # Maybe it's VEDAON_...
    # Extact digits
    import re
    digits = re.findall(r'\d+', target_username)
    if digits:
         numeric_part = digits[0]
         similar = User.objects.filter(username__icontains=numeric_part)
         for u in similar:
             print(f"Found similar user: {u.username}")
             # Optional: Auto-fix if only one match? No, safer to ask.
