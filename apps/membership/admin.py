from django.contrib import admin
from .models import MembershipTask, MembershipTaskSubmission, CreatorMembership


class MembershipTaskSubmissionInline(admin.TabularInline):
    model = MembershipTaskSubmission
    extra = 0
    readonly_fields = ['submitted_at', 'reviewed_at']


@admin.register(MembershipTask)
class MembershipTaskAdmin(admin.ModelAdmin):
    list_display = ['brand_name', 'title', 'platform', 'points_value', 'is_active', 'is_featured', 'created_at']
    list_filter = ['platform', 'is_active', 'is_featured', 'created_at']
    search_fields = ['brand_name', 'title']
    inlines = [MembershipTaskSubmissionInline]


@admin.register(MembershipTaskSubmission)
class MembershipTaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ['task', 'creator', 'status', 'points_awarded', 'submitted_at', 'reviewed_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['task__title', 'creator__email']
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        for submission in queryset.filter(status='pending'):
            submission.status = 'approved'
            submission.points_awarded = submission.task.points_value
            submission.reviewer = request.user
            submission.reviewed_at = timezone.now()
            submission.save()

            if hasattr(submission.creator, 'membership'):
                submission.creator.membership.add_points(submission.task.points_value)
    approve_selected.short_description = "Approve selected submissions"

    def reject_selected(self, request, queryset):
        queryset.filter(status='pending').update(
            status='rejected',
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
    reject_selected.short_description = "Reject selected submissions"


@admin.register(CreatorMembership)
class CreatorMembershipAdmin(admin.ModelAdmin):
    list_display = ['creator', 'total_points', 'pro_active', 'tier', 'updated_at']
    list_filter = ['pro_active', 'tier', 'updated_at']
    search_fields = ['creator__email', 'creator__username']


from django.utils import timezone
