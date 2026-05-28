from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SocialAccount, BrandProfile, CreatorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'name', 'role', 'is_verified', 'barter_score', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'name']
    ordering = ['-created_at']
    fieldsets = [
        (None, {'fields': ['email', 'password']}),
        ('Personal info', {'fields': ['name', 'username', 'bio', 'location_city', 'location_country', 'profile_photo_url']}),
        ('Barter', {'fields': ['role', 'is_verified', 'barter_score']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Important dates', {'fields': ['last_login', 'created_at', 'updated_at']}),
    ]
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': ['email', 'name', 'username', 'role', 'password1', 'password2'],
        }),
    ]


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'handle', 'followers', 'engagement_rate', 'last_synced']
    list_filter = ['platform', 'created_at']
    search_fields = ['user__email', 'handle']
    ordering = ['-followers']


@admin.register(BrandProfile)
class BrandProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'website', 'domain_verified', 'created_at']
    list_filter = ['domain_verified', 'created_at']
    search_fields = ['user__email', 'company_name']


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'created_at']
    list_filter = ['tier', 'created_at']
    search_fields = ['user__email', 'user__username']
