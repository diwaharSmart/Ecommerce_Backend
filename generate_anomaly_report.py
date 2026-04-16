import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Transaction, Profile

def generate_anomaly_report():
    print("Generating detailed anomaly report...")
    transactions = Transaction.objects.filter(type='binary_income').order_by('id')
    
    # We will aggregate by user
    anomalous_users = {}
    
    for t in transactions:
        desc = t.description
        match = re.search(r'Deducted L:(\d+) R:(\d+)', desc)
        if match:
            deduct_l = int(match.group(1))
            deduct_r = int(match.group(2))
            
            if deduct_l == 200 or deduct_r == 200:
                user = t.user
                if user.id not in anomalous_users:
                    # Calculate total pair matches for this user across all their binary transactions
                    user_binary_txns = Transaction.objects.filter(user=user, type='binary_income')
                    total_pairs = 0
                    for utx in user_binary_txns:
                        pairs_match = re.search(r'for (\d+) pairs', utx.description)
                        if pairs_match:
                            total_pairs += int(pairs_match.group(1))
                    
                    anomalous_users[user.id] = {
                        'username': user.username,
                        'total_pairs': total_pairs,
                        'anomalous_txns': []
                    }
                
                # Add the specific anomaly record
                anomalous_users[user.id]['anomalous_txns'].append({
                    'txn_id': t.id,
                    'desc': desc
                })

    # Write to a clean text file
    with open('anomaly_report.txt', 'w') as f:
        f.write("=== USERS WITH 200 PV DEDUCTION ANOMALY ===\n\n")
        
        for uid, data in anomalous_users.items():
            f.write(f"User ID: {uid} | Username: {data['username']} | Total Pair Matches (Lifetime): {data['total_pairs']}\n")
            f.write("Errors Detected:\n")
            for at in data['anomalous_txns']:
                f.write(f"  - Txn #{at['txn_id']}: {at['desc']}\n")
            f.write("\n" + "-"*60 + "\n\n")
            
    print(f"Report saved to anomaly_report.txt containing {len(anomalous_users)} affected users.")

if __name__ == '__main__':
    generate_anomaly_report()
