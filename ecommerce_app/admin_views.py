from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from ecommerce_app.models import KYC, Wallet, Transaction, WithdrawalRequest, OrderItem
from django.db.models import Sum, Q, F, ExpressionWrapper, DecimalField
from decimal import Decimal
import datetime
from django.utils import timezone
from django.utils.dateparse import parse_date

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
    today = timezone.now()
    default_start = today - datetime.timedelta(days=today.weekday())
    default_start = default_start.replace(hour=0, minute=0, second=0, microsecond=0)
    default_end = default_start + datetime.timedelta(days=6)
    default_end = default_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str:
        start_date = parse_date(start_date_str)
        start_datetime = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    else:
        start_date = default_start.date()
        start_datetime = default_start
        
    if end_date_str:
        end_date = parse_date(end_date_str)
        end_datetime = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))
    else:
        end_date = default_end.date()
        end_datetime = default_end

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
    
    global_total_income = Decimal('0.00')
    global_total_binary = Decimal('0.00')
    global_total_level = Decimal('0.00')
    global_total_withdrawals = Decimal('0.00')
    global_remaining = Decimal('0.00')
    
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
                
        total_income = Decimal('0.00')
        total_binary = Decimal('0.00')
        total_level = Decimal('0.00')
        total_withdrawals = Decimal('0.00')
        
        for user in group:
            binary_inc = Transaction.objects.filter(
                user=user, type='binary_income', direction='credit',
                created_at__range=(start_datetime, end_datetime)
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_binary += binary_inc
            
            level_inc = Transaction.objects.filter(
                user=user, type='level_income', direction='credit',
                created_at__range=(start_datetime, end_datetime)
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_level += level_inc
            
            withdrawals_sum = WithdrawalRequest.objects.filter(
                user=user, status='approved',
                created_at__range=(start_datetime, end_datetime)
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
            total_withdrawals += withdrawals_sum
            
            total_income += (binary_inc + level_inc)
            
        remaining_balance = total_income - total_withdrawals
        
        if total_income > 0:
            global_total_income += total_income
            global_total_binary += total_binary
            global_total_level += total_level
            global_total_withdrawals += total_withdrawals
            global_remaining += remaining_balance
            
            payout_groups.append({
                'mobile': phone,
                'accounts_count': len(group),
                'names': ", ".join(sorted(list(set([f"{u.first_name} {u.last_name}".strip() for u in group if u.first_name])))),
                'usernames': ", ".join(sorted([u.username for u in group])),
                'bank_name': shared_bank_name,
                'account_number': shared_bank_acc,
                'ifsc_code': shared_ifsc,
                'total_income': total_income,
                'total_binary': total_binary,
                'total_level': total_level,
                'total_withdrawals': total_withdrawals,
                'remaining_balance': remaining_balance,
                'has_kyc': has_kyc
            })
        
    payout_groups.sort(key=lambda x: x['total_income'], reverse=True)
    

    # --- Analytics Calculations ---
    # KYC Stats
    all_valid_users = User.objects.exclude(is_superuser=True).exclude(username='admin')
    kyc_verified_users = all_valid_users.filter(kyc__bank_account_number__isnull=False).exclude(kyc__bank_account_number='')
    total_kyc_verified = kyc_verified_users.count()
    total_kyc_unverified = all_valid_users.count() - total_kyc_verified
    
    # Turnover Stats for selected Date Range
    valid_orders = OrderItem.objects.filter(
        order__status__in=['paid', 'completed'], product__pv__gt=1, 
        order__created_at__range=(start_datetime, end_datetime)
    ).annotate(
        total_cost=ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())
    ).aggregate(Sum('total_cost'))['total_cost__sum'] or Decimal('0.00')
    
    pin_purchases = Transaction.objects.filter(
        type='pin_purchase', direction='debit', 
        created_at__range=(start_datetime, end_datetime)
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    total_sales_revenue = valid_orders + pin_purchases
    company_turnover = total_sales_revenue - global_total_income
    
    context = {
        'payout_groups': payout_groups,
        'title': 'Weekly Payouts',
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'global_total_income': global_total_income,
        'global_total_binary': global_total_binary,
        'global_total_level': global_total_level,
        'total_kyc_verified': total_kyc_verified,
        'total_kyc_unverified': total_kyc_unverified,
        'total_sales_revenue': total_sales_revenue,
        'company_turnover': company_turnover,
        'global_total_withdrawals': global_total_withdrawals,
        'global_remaining': global_remaining,
    }
    return render(request, 'admin/weekly_payouts_list.html', context)


def get_descendants(profile):
    descendants = []
    children = profile.children.all().select_related('user')
    for child in children:
        descendants.append(child)
        descendants.extend(get_descendants(child))
    return descendants

@staff_member_required
def weekly_payouts_detail(request, mobile):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        messages.error(request, "Date range is required to view details.")
        return redirect('weekly_payouts_list')
        
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    start_datetime = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_datetime = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))

    users = User.objects.all().prefetch_related('kyc')
    group = []
    
    for user in users:
        extracted = extract_mobile(user)
        if extracted == mobile and not user.is_superuser and user.username != 'admin':
            group.append(user)
            
    if not group:
        messages.error(request, "No users found for this mobile number.")
        return redirect('weekly_payouts_list')
        
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
        return redirect('weekly_payouts_list')
        
    accounts_data = []
    total_group_remaining = Decimal('0.00')
    
    for user in group:
        binary_inc = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit',
            created_at__range=(start_datetime, end_datetime)
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        level_inc = Transaction.objects.filter(
            user=user, type='level_income', direction='credit',
            created_at__range=(start_datetime, end_datetime)
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        withdrawals_sum = WithdrawalRequest.objects.filter(
            user=user, status='approved',
            created_at__range=(start_datetime, end_datetime)
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        income = binary_inc + level_inc
        remaining = income - withdrawals_sum
        total_group_remaining += remaining
        
        binary_txns = Transaction.objects.filter(
            user=user, type='binary_income', direction='credit',
            created_at__range=(start_datetime, end_datetime)
        ).order_by('-created_at')
        
        level_txns = Transaction.objects.filter(
            user=user, type='level_income', direction='credit',
            created_at__range=(start_datetime, end_datetime)
        ).order_by('-created_at')
        
        # --- Team Purchase PV Calculation ---
        try:
            profile = user.profile
            left_child = profile.children.filter(position='L').first()
            right_child = profile.children.filter(position='R').first()
            
            left_descendants = [left_child] + get_descendants(left_child) if left_child else []
            right_descendants = [right_child] + get_descendants(right_child) if right_child else []
            
            left_users = [p.user for p in left_descendants]
            right_users = [p.user for p in right_descendants]
            
            from ecommerce_app.models import Order
            
            left_orders = Order.objects.filter(
                user__in=left_users,
                status__in=['paid', 'completed'],
                created_at__range=(start_datetime, end_datetime)
            ).order_by('-created_at')
            
            right_orders = Order.objects.filter(
                user__in=right_users,
                status__in=['paid', 'completed'],
                created_at__range=(start_datetime, end_datetime)
            ).order_by('-created_at')
            
            left_pv_sum = sum(o.total_pv for o in left_orders)
            right_pv_sum = sum(o.total_pv for o in right_orders)
            
            order_history = []
            for o in left_orders:
                order_history.append({
                    'date': o.created_at,
                    'side': 'Left',
                    'username': o.user.username,
                    'first_name': o.user.first_name,
                    'amount': o.total_amount,
                    'pv': o.total_pv
                })
            for o in right_orders:
                order_history.append({
                    'date': o.created_at,
                    'side': 'Right',
                    'username': o.user.username,
                    'first_name': o.user.first_name,
                    'amount': o.total_amount,
                    'pv': o.total_pv
                })
                
            # Sort all combined orders by date descending
            order_history.sort(key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            left_pv_sum = 0
            right_pv_sum = 0
            order_history = []
        
        accounts_data.append({
            'user': user,
            'income': income,
            'binary_income': binary_inc,
            'level_income': level_inc,
            'withdrawals': withdrawals_sum,
            'remaining': remaining,
            'binary_txns': binary_txns,
            'level_txns': level_txns,
            'left_pv_sum': left_pv_sum,
            'right_pv_sum': right_pv_sum,
            'order_history': order_history,
        })
        
    if request.method == 'POST':
        if 'initiate_withdrawal' in request.POST:
            withdrawals_created = 0
            for data in accounts_data:
                usr = data['user']
                rem = data['remaining']
                if rem > 0:
                    total_amount = rem
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
                        admin_remark=f'Weekly Payout ({start_date_str} to {end_date_str})'
                    )
                    
                    # Backdate to the end of the selected week
                    WithdrawalRequest.objects.filter(id=req.id).update(created_at=end_datetime, updated_at=end_datetime)
                    Transaction.objects.filter(related_withdrawal=req).update(created_at=end_datetime)
                    
                    withdrawals_created += 1
                    
            messages.success(request, f"Successfully processed {withdrawals_created} withdrawal(s). Wallets have been updated.")
            return redirect(f"/admin/payouts/weekly/?start_date={start_date_str}&end_date={end_date_str}")

    total_after_deduction = total_group_remaining * Decimal('0.80')
    
    context = {
        'group': accounts_data,
        'mobile': mobile,
        'kyc': shared_kyc,
        'total_group_remaining': total_group_remaining,
        'total_after_deduction': total_after_deduction,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'title': f'Payout Details for {mobile}',
    }
    return render(request, 'admin/weekly_payouts_detail.html', context)


@staff_member_required
def admin_manual_transaction(request):
    search_query = request.GET.get('search_query', '')
    target_user = None
    if search_query:
        target_user = User.objects.filter(username=search_query).first()
        if not target_user:
            messages.error(request, f"User '{search_query}' not found.")

    if request.method == 'POST' and 'create_transaction' in request.POST:
        user_id = request.POST.get('user_id')
        t_type = request.POST.get('type')
        t_dir = request.POST.get('direction')
        amount = request.POST.get('amount')
        desc = request.POST.get('description', 'Manual Admin Transaction')

        try:
            usr = User.objects.get(id=user_id)
            Transaction.objects.create(
                user=usr,
                amount=Decimal(amount),
                type=t_type,
                direction=t_dir,
                description=desc
            )
            messages.success(request, f"Successfully created {t_dir} transaction for {usr.username}.")
            return redirect(f"/admin/payouts/manual-transaction/?search_query={usr.username}")
        except Exception as e:
            messages.error(request, f"Error creating transaction: {str(e)}")

    context = {
        'title': 'Manual Transaction Management',
        'target_user': target_user,
        'search_query': search_query,
    }
    return render(request, 'admin/manual_transaction.html', context)


@staff_member_required
def admin_manual_transaction_history(request):
    # Filter for transactions that are likely manual or specifically 'account_closing'
    manual_types = ['account_closing', 'deposit', 'withdrawal', 'top_up', 'binary_income', 'level_income']
    # We'll show all but allow filtering by type
    selected_type = request.GET.get('type', '')
    
    txns = Transaction.objects.all().order_by('-created_at')
    
    if selected_type:
        txns = txns.filter(type=selected_type)
    
    # Simple search by username or description
    q = request.GET.get('q', '')
    if q:
        txns = txns.filter(Q(user__username__icontains=q) | Q(description__icontains=q))

    context = {
        'title': 'System Transaction History',
        'transactions': txns[:200], # Limit to last 200 for performance
        'selected_type': selected_type,
        'types': Transaction.TRANSACTION_TYPES,
        'q': q,
    }
    return render(request, 'admin/manual_transaction_history.html', context)
