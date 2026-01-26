from django.contrib import admin
from .models import Category, Product, Profile, Wallet, PayinRequest, Transaction, Coupon, Order, OrderItem, Banner, UserAddress, Cart, CartItem, KYC, SupportTicket

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'pv', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'sponsor', 'parent', 'position', 'is_active', 'package_amount']

class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_balance', 'updated_at']

class PayinRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'reference_number', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'reference_number']

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'amount', 'direction', 'created_at']
    list_filter = ['type', 'direction']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    inlines = [OrderItemInline]

class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'from_date', 'to_date', 'is_active']
    list_filter = ['is_active']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(PayinRequest, PayinRequestAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Coupon)
admin.site.register(Order, OrderAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(UserAddress)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(KYC)
admin.site.register(SupportTicket)
