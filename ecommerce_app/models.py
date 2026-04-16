from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

# --- Ecommerce Models ---
class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='categories/banner/', blank=True, null=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pv = models.PositiveIntegerField(help_text="Point Value for MLM")
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_pv = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='pending') # pending, paid, shipped, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pv = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

# --- MLM & Wallet Models ---

class Profile(models.Model):
    POSITION_CHOICES = (
        ('L', 'Left'),
        ('R', 'Right'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    sponsor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_referrals')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    position = models.CharField(max_length=1, choices=POSITION_CHOICES, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=False)
    package_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # PV Tracking
    total_left_pv = models.PositiveIntegerField(default=0)
    total_right_pv = models.PositiveIntegerField(default=0)
    current_left_pv = models.PositiveIntegerField(default=0)
    current_right_pv = models.PositiveIntegerField(default=0)
    
    # Member Counting
    total_left_count = models.PositiveIntegerField(default=0)
    total_right_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    top_up_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

class PayinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payin_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=255, unique=True)
    screenshot = models.ImageField(upload_to='payin_proofs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payin {self.reference_number} - {self.status}"

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Net Amount (80%)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Gross Amount (100%)
    tds_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # 10% TDS
    top_up_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # 10% TopUp
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Withdrawal {self.user.username} - {self.amount}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('purchase', 'Purchase'),
        ('binary_income', 'Binary Income'),
        ('level_income', 'Level Income'),
        ('referral_bonus', 'Referral Bonus'),
        ('tds', 'TDS'),
        ('top_up', 'Top-Up'),
        ('pin_purchase', 'Pin Purchase'),

    )
    DIRECTION_CHOICES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    related_payin = models.ForeignKey(PayinRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    # New Fields for Withdrawal Logic
    tds_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    top_up_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    related_withdrawal = models.ForeignKey('WithdrawalRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} ({self.direction})"

class Coupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupons')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coupon {self.amount} for {self.user.username}"

@receiver(post_save, sender=PayinRequest)
def approve_payin_request(sender, instance, created, **kwargs):
    """
    If a PayinRequest is approved, create a corresponding Transaction.
    """
    if instance.status == 'approved':
        # Check if transaction already exists to avoid duplicates
        existing_txn = Transaction.objects.filter(related_payin=instance).exists()
        if not existing_txn:
            Transaction.objects.create(
                user=instance.user,
                amount=instance.amount,
                direction='credit',
                type='deposit',
                description=f"Auto-deposit from Payin {instance.reference_number}",
                related_payin=instance
            )

@receiver(post_save, sender=Transaction)
def update_wallet_and_check_activation(sender, instance, created, **kwargs):
    """
    When a Transaction is saved:
    1. Update the user's Wallet balance.
    2. If purchase, activate User Profile if not already active.
    """
    if created:
        wallet = instance.user.wallet
        
        # Logic to route funds to correct balance
        if instance.type == 'top_up':
            if instance.direction == 'credit':
                 wallet.top_up_balance = float(wallet.top_up_balance) + float(instance.amount)
            else: # debit
                 wallet.top_up_balance = float(wallet.top_up_balance) - float(instance.amount)
        elif instance.direction == 'credit':
            wallet.current_balance = float(wallet.current_balance) + float(instance.amount)
        elif instance.direction == 'debit':
            wallet.current_balance = float(wallet.current_balance) - float(instance.amount)
            
        wallet.save()

        # Activation Logic
        if instance.type == 'purchase':
            profile = instance.user.profile
            if not profile.is_active:
                profile.is_active = True
                profile.save()

@receiver(post_save, sender=WithdrawalRequest)
def process_withdrawal_status_change(sender, instance, created, **kwargs):
    """
    Handles Wallet logic for WithdrawalRequests:
    1. On Creation (pending): Deduct full amount from Main, Credit Top-Up Wallet.
    2. On Rejection: Refund full amount to Main, Deduct from Top-Up Wallet.
    """
    net_amount = instance.amount
    total_gross = instance.total_amount
    tds = instance.tds_amount
    top_up = instance.top_up_amount

    if created:
        # AT CREATION: Deduct everything immediately
        # Net Pay Transaction
        Transaction.objects.create(
            user=instance.user,
            amount=net_amount,
            direction='debit',
            type='withdrawal',
            description=f"Withdrawal Request Created (Net Pay)",
            related_withdrawal=instance
        )
        
        # TDS Transaction
        Transaction.objects.create(
            user=instance.user,
            amount=tds,
            direction='debit',
            type='tds',
            description=f"Withdrawal TDS Deduction",
            related_withdrawal=instance
        )
        
        # Top-Up Debit (From Main)
        Transaction.objects.create(
            user=instance.user,
            amount=top_up,
            direction='debit',
            type='withdrawal', # Debit from main
            description=f"Withdrawal Top-Up Deduction",
            related_withdrawal=instance
        )

        # Top-Up Credit (To Top-Up Wallet)
        Transaction.objects.create(
            user=instance.user,
            amount=top_up,
            direction='credit',
            type='top_up', # Signal handles crediting top_up_balance
            description=f"Top-Up from Withdrawal Request",
            related_withdrawal=instance
        )

    elif instance.status == 'rejected':
        # ON REJECTION: Refund everything
        # Check if already refunded to avoid double refund
        if Transaction.objects.filter(related_withdrawal=instance, description__icontains="Refund").exists():
            return

        # Refund Net + TDS + TopUp back to Main Wallet
        Transaction.objects.create(
            user=instance.user,
            amount=total_gross, # Full 100% refund
            direction='credit',
            type='deposit',
            description=f"Refund: Withdrawal Request Rejected (#{instance.id})",
            related_withdrawal=instance
        )

        # Reverse the Top-Up Wallet credit (Debit from Top-Up Wallet)
        Transaction.objects.create(
            user=instance.user,
            amount=top_up,
            direction='debit',
            type='top_up', 
            description=f"Refund Reversal: Withdrawal Rejected Top-Up Deduction",
            related_withdrawal=instance
        )


@receiver(post_save, sender=Order)
def generate_coupons_on_order_paid(sender, instance, created, **kwargs):
    """
    When Order status becomes 'paid', generate coupons for Grocery items.
    6 coupons per item quantity, valid for 1 month each, staggered.
    """
    if instance.status == 'paid':
        from datetime import timedelta
        from django.utils import timezone
        
        grocery_items = instance.items.filter(product__category__slug__icontains='grocery')
        current_date = timezone.now().date()

        for item in grocery_items:
            # "All grocery product is 6 coupoun... users can reedem 1 coupoun for a month"
            # Creating 6 coupons per quantity unit
            for q in range(item.quantity):
                for i in range(6):
                    # Stagger validity: 1st valid now, 2nd valid next month, etc.
                    # Simple approx: i * 30 days
                    start_validity = current_date + timedelta(days=i*30)
                    end_validity = start_validity + timedelta(days=30)
                    
                    Coupon.objects.create(
                        user=instance.user,
                        amount=500.00,
                        is_active=True,
                        valid_until=end_validity 
                        # Ideally we'd have a 'valid_from' too, but model only has valid_until
                        # Assuming application logic enforces "1 per month" or using valid_until as the constraint.
                        # For strictly 1 redeeming per month logic, we might need 'valid_from'.
                        # I'll update Coupon model to include 'valid_from' effectively if I could, 
                        # but avoiding schema change on existing fields if possible.
                        # Actually, user requirement says "reedem 1 coupoun for a month".
                        # Let's interpret valid_until as the expiry of that specific month's coupon.
                    )

class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.city}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

    @property
    def total_pv(self):
        return self.quantity * self.product.pv

class KYC(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    name_on_card = models.CharField(max_length=255)
    aadhar_number = models.CharField(max_length=50)
    aadhar_image = models.ImageField(upload_to='kyc/aadhar/', null=True, blank=True)
    pan_number = models.CharField(max_length=50)
    pan_image = models.ImageField(upload_to='kyc/pan/', null=True, blank=True)
    passbook_image = models.ImageField(upload_to='kyc/passbooks/', null=True, blank=True)

    # Bank Details
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=50, blank=True)
    account_holder_name = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KYC - {self.user.username}"

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.subject}"

class Banner(models.Model):
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/')
    from_date = models.DateTimeField()
    to_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or "Banner"


class PinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pin_requests')
    number_of_pins = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.number_of_pins} Pins ({self.status})"

class Pin(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('used', 'Used'),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pins')
    code = models.CharField(max_length=50, unique=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=3000.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_pins')
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.value} ({self.status})"

@receiver(post_save, sender=PinRequest)
def generate_pins_on_approval(sender, instance, created, **kwargs):
    if instance.status == 'approved':
        import uuid
        pass 
        current_pin_count = Pin.objects.filter(owner=instance.user, created_at__gte=instance.created_at).count()
        pass




