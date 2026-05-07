from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    CategoryViewSet, ProductViewSet, ProfileViewSet, 
    WalletViewSet, PayinRequestViewSet, TransactionViewSet, CouponViewSet, OrderViewSet, BannerViewSet,
    UserAddressViewSet, CartViewSet, CheckoutViewSet, KYCViewSet, SupportTicketViewSet, HomeAPIView, WithdrawalRequestViewSet
)

router = DefaultRouter()
router.register(r'withdrawal-requests', WithdrawalRequestViewSet, basename='withdrawal-requests')
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'wallet', WalletViewSet)
router.register(r'payins', PayinRequestViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'banners', BannerViewSet)
router.register(r'user-addresses', UserAddressViewSet, basename='user-addresses')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'checkout', CheckoutViewSet, basename='checkout')
router.register(r'kyc', KYCViewSet, basename='kyc')
router.register(r'support-tickets', SupportTicketViewSet, basename='support-tickets')

urlpatterns = [
    path('api/home/', HomeAPIView.as_view(), name='home-api'),
    path('api/', include(router.urls)),
    
    # Custom Admin Views
    path('admin/payouts/weekly/', __import__('ecommerce_app.admin_views').admin_views.weekly_payouts_list, name='weekly_payouts_list'),
    path('admin/payouts/weekly/<str:mobile>/', __import__('ecommerce_app.admin_views').admin_views.weekly_payouts_detail, name='weekly_payouts_detail'),
]
