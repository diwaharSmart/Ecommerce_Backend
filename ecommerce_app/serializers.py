from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Product, Profile, Wallet, PayinRequest, Transaction, Coupon, Order, OrderItem, Banner, UserAddress, Cart, CartItem, KYC, SupportTicket, WithdrawalRequest
from django.db.models import Sum

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    sponsor_username = serializers.ReadOnlyField(source='sponsor.user.username')
    sponsor_first_name = serializers.ReadOnlyField(source='sponsor.user.first_name')
    sponsor_id = serializers.ReadOnlyField(source='sponsor.user.username') # Alias for clarity if needed, or use sponsor_username
    parent_username = serializers.ReadOnlyField(source='parent.user.username')
    
    total_team_size = serializers.SerializerMethodField()
    total_earning = serializers.SerializerMethodField()
    kyc_status = serializers.SerializerMethodField()
    total_earning_by_type = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'

    def get_total_team_size(self, obj):
        return obj.total_left_count + obj.total_right_count

    def get_kyc_status(self, obj):
        # Access KYC status via reverse relation 'kyc' (OneToOne)
        try:
            return obj.user.kyc.status
        except KYC.DoesNotExist:
            return "not_submitted"

    def get_total_earning(self, obj):
        # Sum of specific income types
        income_types = ['binary_income', 'level_income', 'referral_bonus']
        total = Transaction.objects.filter(
            user=obj.user, 
            type__in=income_types, 
            direction='credit'
        ).aggregate(sum_val=Sum('amount'))['sum_val']
        return total or 0.0

    def get_total_earning_by_type(self, obj):
        # Break down earning by type
        income_types = ['binary_income', 'level_income', 'referral_bonus']
        breakdown = {}
        for t in income_types:
             val = Transaction.objects.filter(
                user=obj.user, 
                type=t, 
                direction='credit'
            ).aggregate(sum_val=Sum('amount'))['sum_val'] or 0.0
             breakdown[t] = val
        return breakdown

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = '__all__'

class WalletSerializer(serializers.ModelSerializer):
    calculated_balance = serializers.SerializerMethodField()
    transaction_sums = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = '__all__'

    def get_calculated_balance(self, obj):
        # Credits: Exclude 'top_up' credits as they go to top_up_balance
        credits = Transaction.objects.filter(
            user=obj.user, 
            direction='credit'
        ).exclude(type='top_up').aggregate(s=Sum('amount'))['s'] or 0
        
        debits = Transaction.objects.filter(
            user=obj.user, 
            direction='debit'
        ).aggregate(s=Sum('amount'))['s'] or 0
        
        return credits - debits

    def get_transaction_sums(self, obj):
        types = [
            'purchase', 'deposit', 'withdrawal', 
            'binary_income', 'level_income', 'referral_bonus',
            'tds', 'top_up'
        ]
        sums = {}
        for t in types:
            val = Transaction.objects.filter(user=obj.user, type=t).aggregate(s=Sum('amount'))['s'] or 0
            sums[f"total_{t}"] = val
        return sums

class PayinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayinRequest
        fields = '__all__'

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    bank_details = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalRequest
        fields = '__all__'
        read_only_fields = ['status', 'admin_remark']

    def get_bank_details(self, obj):
        try:
            kyc = KYC.objects.get(user=obj.user)
            return {
                "bank_name": kyc.bank_name,
                "bank_account_number": kyc.bank_account_number,
                "ifsc_code": kyc.ifsc_code,
                "account_holder_name": kyc.account_holder_name
            }
        except KYC.DoesNotExist:
            return None

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        exclude = ['user']

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_pv = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'total_pv', 'created_at']

    def get_total_price(self, obj):
        return sum(item.total_price for item in obj.items.all())

    def get_total_pv(self, obj):
        return sum(item.total_pv for item in obj.items.all())

class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = '__all__'
        read_only_fields = ['status', 'admin_remark']
        exclude = ['user']

class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['status']
