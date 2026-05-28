from django.contrib import admin
from .models import Proposal, ProposalCounter


class ProposalCounterInline(admin.TabularInline):
    model = ProposalCounter
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['id', 'offer', 'creator', 'status', 'round_number', 'created_at']
    list_filter = ['status', 'round_number', 'created_at']
    search_fields = ['offer__title', 'creator__email', 'creator__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'expires_at']
    inlines = [ProposalCounterInline]
    fieldsets = [
        ('Basic Info', {
            'fields': ['id', 'offer', 'creator', 'pitch', 'status', 'round_number']
        }),
        ('Terms', {
            'fields': ['deliverables', 'timeline']
        }),
        ('Counter Info', {
            'fields': ['counter_by', 'expires_at']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]


@admin.register(ProposalCounter)
class ProposalCounterAdmin(admin.ModelAdmin):
    list_display = ['proposal', 'sent_by', 'round_number', 'created_at']
    list_filter = ['round_number', 'created_at']
    search_fields = ['proposal__id', 'sent_by__email']
    readonly_fields = ['created_at']
