from django.urls import path
from . import views

urlpatterns = [
    path('create-deal-fee/', views.CreateDealFeePaymentView.as_view(), name='payment-create'),
    path('webhook/razorpay/', views.RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    path('webhook/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('invoices/', views.InvoiceListView.as_view(), name='payment-invoices'),
    path('subscriptions/', views.SubscriptionCreateView.as_view(), name='subscription-create'),
    path('subscriptions/me/', views.MySubscriptionView.as_view(), name='subscription-me'),
    path('subscriptions/me/cancel/', views.CancelSubscriptionView.as_view(), name='subscription-cancel'),
    path('wallet/', views.MyWalletView.as_view(), name='wallet'),
    path('wallet/transactions/', views.WalletTransactionsView.as_view(), name='wallet-transactions'),
    path('wallet/transfer/', views.TransferPointsView.as_view(), name='wallet-transfer'),
]
