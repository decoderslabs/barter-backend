from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'type', 'estimated_value', 'currency', 'status', 'quantity_remaining', 'created_at']
    list_filter = ['type', 'status', 'currency', 'rights_tier', 'exclusivity', 'created_at']
    search_fields = ['title', 'description', 'brand__email', 'brand__username']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = [
        ('Basic Info', {
            'fields': ['id', 'brand', 'type', 'title', 'description', 'status']
        }),
        ('Value', {
            'fields': ['estimated_value', 'currency', 'quantity', 'quantity_remaining']
        }),
        ('Requirements', {
            'fields': ['content_ask', 'kpi_preferences', 'rights_tier', 'raw_files_required', 'exclusivity']
        }),
        ('Media', {
            'fields': ['images', 'attachments']
        }),
        ('Proposals', {
            'fields': ['proposal_deadline', 'max_proposals', 'shipping_required']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
