from django.contrib import admin
from .models import DropsCampaign, DropsApplication


class DropsApplicationInline(admin.TabularInline):
    model = DropsApplication
    extra = 0
    readonly_fields = ['applied_at', 'reviewed_at']


@admin.register(DropsCampaign)
class DropsCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'goal', 'total_slots', 'filled_slots', 'status', 'created_at']
    list_filter = ['goal', 'status', 'approval_mode', 'created_at']
    search_fields = ['name', 'brand__email']
    inlines = [DropsApplicationInline]


@admin.register(DropsApplication)
class DropsApplicationAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'creator', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['campaign__name', 'creator__email']
