from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from ecommerce_app.models import KYC, Wallet, Transaction, WithdrawalRequest
from django.db.models import Sum
from decimal import Decimal
import datetime

def extract_mobile(user):
    username = user.username.lower()
    email = user.email.lower()
    
    if '@' in username:
        username_part = username.split('@')[0]
    else:
        username_part = username
        
    if '@' in email:
        email_part = email.split('@')[0]
    else:
        email_part = email
        
    if username_part.isdigit() and len(username_part) >= 5:
        return username_part
    if email_part.isdigit() and len(email_part) >= 5:
        return email_part
        
    return username_part

@staff_member_required
def weekly_payouts_list(request):
    users = User.objects.all().prefetch_related('kyc')
    mobile_groups = {}
    
    for user in users:
        mobile = extract_mobile(user)
        if user.is_superuser or user.username == 'admin' or len(mobile) < 5:
            continue
            
        if mobile not in mobile_groups:
            mobile_groups[mobile] = []
        mobile_groups[mobile].append(user)
        
    payout_groups = []
    
    for phone, group in mobile_groups.items():
        shared_bank_acc = "N/A"
        shared_bank_name = "N/A"
        shared_ifsc = "N/A"
        has_kyc = False
        
        for u in group:
            try:
                if hasattr(u, 'kyc'):
                    kyc = u.kyc
                    if kyc.bank_account_number and kyc.bank_account_number.strip():
                        shared_bank_acc = kyc.bank_account_number
                        shared_bank_name = kyc.bank_name
                        shared_ifsc = kyc.ifsc_code
                        has_kyc = True
                        break 
            except Exception:
                pass
                
        if not has_kyc:
            continue
            
        total_income = Decimal('0.00')
        total_binary = Decimal('0.00')
        total_level = Decimal('0.00')
        
        for user in group:
            binary_inc = Transaction.objects.filter(
                user=user, type='binary_income', direction='credit'
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_binary += binary_inc
            
            level_inc = Transaction.objects.filter(
                user=user, type='level_income', direction='credit'
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_level += level_inc
            
            total_income += (binary_inc + level_inc)
            
        if total_income > 0:
            payout_groups.append({
                'mobile': phone,
                'accounts_count': len(group),
                'bank_name': shared_bank_name,
                'account_number': shared_bank_acc,
                'ifsc_code': shared_ifsc,
                'total_income': total_income,
                'total_binary': total_binary,
                'total_level': total_level
            })
        
    # Sort by total income descending
    payout_groups.sort(key=lambda x: x['total_income'], reverse=True)
        
    context = {
        'payout_groups': payout_groups,
        'title': 'Weekly Payouts',
    }
    return render(request, 'admin/weekly_payouts_list.html', context)

@staff_member_required
def weekly_payouts_detail(request, mobile):
    users = User.objects.all().prefetch_related('kyc')
    group = []
    
    for user in users:
        extracted = extract_mobile(user)
        if extracted == mobile and not user.is_superuser and user.username != 'admin':
            group.append(user)
            
    if not group:
        messages.error(request, "No users found for this mobile number.")
        return redirect('admin:weekly_payouts_list')
        
    shared_kyc = None
    
    for u in group:
        try:
            if hasattr(u, 'kyc'):
                kyc = u.kyc
                if kyc.bank_account_number and kyc.bank_account_number.strip():
                    shared_kyc = kyc
                    break 
        except Exception:
            pass
            
    if not shared_kyc:
        messages.error(request, "No KYC found for this group.")
        return redirect('admin:weekly_payouts_list')
        
    accounts_data = []
    total_group_income = Decimal('0.00')
    
    for user in group:
        binary_inc = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        level_inc = Transaction.objects.filter(
            user=user, type='level_income', direction='credit'
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        income = binary_inc + level_inc
        total_group_income += income
        
        accounts_data.append({
            'user': user,
            'income': income,
            'binary_income': binary_inc,
            'level_income': level_inc,
        })
        
    if request.method == 'POST':
        if 'initiate_withdrawal' in request.POST:
            withdrawals_created = 0
            for data in accounts_data:
                usr = data['user']
                inc = data['income']
                if inc > 0:
                    # Create withdrawal request for the combined binary and level income
                    total_amount = inc
                    tds = total_amount * Decimal('0.10')
                    top_up = total_amount * Decimal('0.10')
                    net_amount = total_amount - tds - top_up
                    
                    req = WithdrawalRequest.objects.create(
                        user=usr,
                        total_amount=total_amount,
                        tds_amount=tds,
                        top_up_amount=top_up,
                        amount=net_amount,
                        status='approved',
                        admin_remark='Bulk admin withdrawal (Weekly Payouts)'
                    )
                    withdrawals_created += 1
                    
            messages.success(request, f"Successfully processed {withdrawals_created} withdrawal(s). Wallets have been updated.")
            return redirect('admin:weekly_payouts_list')

    context = {
        'mobile': mobile,
        'group': accounts_data,
        'kyc': shared_kyc,
        'total_group_income': total_group_income,
        'title': f'Payout Details for {mobile}',
    }
    return render(request, 'admin/weekly_payouts_detail.html', context)
