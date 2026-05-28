from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['deal', 'rater', 'ratee', 'stars', 'published_at', 'created_at']
    list_filter = ['stars', 'published_at', 'created_at']
    search_fields = ['rater__email', 'ratee__email', 'review_text']
    readonly_fields = ['created_at', 'published_at']
