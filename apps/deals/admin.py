from django.contrib import admin
from .models import Deal, Delivery, DealMessage, RevisionRequest


class DeliveryInline(admin.TabularInline):
    model = Delivery
    extra = 0
    readonly_fields = ['submitted_at']


class DealMessageInline(admin.TabularInline):
    model = DealMessage
    extra = 0
    readonly_fields = ['created_at', 'read_at']


class RevisionRequestInline(admin.TabularInline):
    model = RevisionRequest
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['id', 'offer', 'brand', 'creator', 'status', 'deal_fee', 'currency', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['offer__title', 'brand__email', 'creator__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'shipped_at', 'delivered_at', 'completed_at']
    inlines = [DeliveryInline, DealMessageInline, RevisionRequestInline]
    fieldsets = [
        ('Basic Info', {
            'fields': ['id', 'offer', 'proposal', 'brand', 'creator', 'status']
        }),
        ('Terms', {
            'fields': ['agreed_terms', 'rights_tier', 'raw_files_required', 'exclusivity']
        }),
        ('Payment', {
            'fields': ['deal_fee', 'currency']
        }),
        ('Shipping', {
            'fields': ['shipping_address', 'shipped_at']
        }),
        ('Delivery', {
            'fields': ['delivered_at', 'completed_at', 'deadline']
        }),
        ('Contract', {
            'fields': ['contract_url']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['deal', 'status', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    readonly_fields = ['submitted_at']


@admin.register(DealMessage)
class DealMessageAdmin(admin.ModelAdmin):
    list_display = ['deal', 'sender', 'body_preview', 'created_at', 'read_at']
    list_filter = ['created_at']
    search_fields = ['body', 'sender__email']
    readonly_fields = ['created_at', 'read_at']

    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body


@admin.register(RevisionRequest)
class RevisionRequestAdmin(admin.ModelAdmin):
    list_display = ['deal', 'requested_by', 'round_number', 'created_at']
    list_filter = ['round_number', 'created_at']
    readonly_fields = ['created_at']
