from django.contrib import admin
from .models import Payment, Subscription, Wallet, WalletTransaction


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['brand', 'deal', 'amount', 'currency', 'gateway', 'status', 'created_at']
    list_filter = ['gateway', 'status', 'currency', 'created_at']
    search_fields = ['brand__email', 'gateway_ref']
    readonly_fields = ['created_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['brand', 'plan', 'gateway', 'status', 'current_period_end', 'deals_used', 'deals_included']
    list_filter = ['plan', 'status', 'gateway', 'created_at']
    search_fields = ['brand__email', 'gateway_sub_id']


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'lifetime_earned', 'lifetime_spent', 'updated_at']
    search_fields = ['user__email', 'user__username']
    inlines = [WalletTransactionInline]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'type', 'amount', 'description', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['wallet__user__email', 'description']
