import os
import django
import csv
import re

# Force the system to use the SQLite UAT Database
os.environ['USE_UAT_DB'] = '1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from ecommerce_app.models import Transaction

def generate_reports():
    print("Generating CSV Reports for UAT Data...")

    binary_transactions = Transaction.objects.filter(type='binary_income').order_by('id')
    level_transactions = Transaction.objects.filter(type='level_income').order_by('id')

    # 1. Binary Income CSV
    with open('binary_income_report.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Transaction ID', 'User ID', 'Username', 'Amount (Rs)', 'Pairs Matched', 'Deducted Left PV', 'Deducted Right PV', 'Date'])
        
        for t in binary_transactions:
            # Expected description: "Binary match reward for 1 pairs (Deducted L:200 R:100)"
            desc = t.description
            pairs = 0
            deduct_l = 0
            deduct_r = 0
            
            match = re.search(r'for (\d+) pairs \(Deducted L:(\d+) R:(\d+)\)', desc)
            if match:
                pairs = match.group(1)
                deduct_l = match.group(2)
                deduct_r = match.group(3)
                
            writer.writerow([t.id, t.user.id, t.user.username, t.amount, pairs, deduct_l, deduct_r, t.created_at.strftime("%Y-%m-%d %H:%M:%S")])
            
    print(f"[SUCCESS] Generated binary_income_report.csv with {binary_transactions.count()} records.")

    # 2. Level Income CSV
    with open('level_income_report.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Transaction ID', 'Receiver User ID', 'Receiver Username', 'Amount (Rs)', 'Level', 'Source Binary Earner', 'Date'])
        
        for t in level_transactions:
            # Expected description: "Level 1 Matching Income from user_uat_1234's Binary Match"
            desc = t.description
            level = ""
            source_user = ""
            
            match = re.search(r'Level (\d+) Matching Income from (.+)\'s Binary Match', desc)
            if match:
                level = match.group(1)
                source_user = match.group(2)
                
            writer.writerow([t.id, t.user.id, t.user.username, t.amount, level, source_user, t.created_at.strftime("%Y-%m-%d %H:%M:%S")])
            
    print(f"[SUCCESS] Generated level_income_report.csv with {level_transactions.count()} records.")

    # 3. User Summary CSV
    from ecommerce_app.models import Profile
    from django.db.models import Sum
    
    profiles = Profile.objects.all().order_by('id')
    grand_total_earnings = 0
    grand_total_pairs = 0
    
    with open('user_summary_report.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['User ID', 'Username', 'Left Count', 'Right Count', 'Total Pair Matches', 'Total Earnings (Rs)'])
        
        for p in profiles:
            user = p.user
            # Calculate total earnings (Binary + Level)
            earnings = Transaction.objects.filter(
                user=user, 
                type__in=['binary_income', 'level_income']
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Calculate total pair matches from binary transactions
            user_binary_tx = Transaction.objects.filter(user=user, type='binary_income')
            user_pairs = 0
            for tx in user_binary_tx:
                match = re.search(r'for (\d+) pairs', tx.description)
                if match:
                    user_pairs += int(match.group(1))
                    
            grand_total_earnings += earnings
            grand_total_pairs += user_pairs
            
            writer.writerow([
                user.id, 
                user.username, 
                p.total_left_count, 
                p.total_right_count, 
                user_pairs, 
                earnings
            ])
        
        # Add Grand Total Row
        writer.writerow([])
        writer.writerow(['GRAND TOTAL', '', '', '', grand_total_pairs, grand_total_earnings])
        
    print(f"[SUCCESS] Generated user_summary_report.csv for {profiles.count()} users.")
    print(f"\n--- GRAND TOTALS ---")
    print(f"Total Pair Matches Across Network: {grand_total_pairs}")
    print(f"Total User Earnings Distributed: Rs. {grand_total_earnings}")
    
if __name__ == '__main__':
    generate_reports()
