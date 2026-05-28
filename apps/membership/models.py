import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class MembershipTask(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('open', 'Open'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand_name = models.CharField(max_length=100)
    brand_logo_url = models.URLField(blank=True)
    title = models.CharField(max_length=200)
    platform = models.CharField(max_length=15, choices=PLATFORM_CHOICES, default='open')
    points_value = models.PositiveIntegerField()
    brief_richtext = models.TextField()
    required_tags = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    available_to_tiers = models.JSONField(default=list)  # ["nano","micro",...]
    available_to_markets = models.JSONField(default=list)  # ["IN","AE",...]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'membership_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand_name}: {self.title} ({self.points_value} pts)"


class MembershipTaskSubmission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit_requested', 'Resubmit Requested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_submissions')
    task = models.ForeignKey(MembershipTask, on_delete=models.CASCADE, related_name='submissions')
    post_url = models.URLField()
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    points_awarded = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'membership_task_submissions'
        ordering = ['-submitted_at']
        unique_together = ['creator', 'task']

    def __str__(self):
        return f"Submission by {self.creator.username} for {self.task.title}"


class CreatorMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membership')
    total_points = models.PositiveIntegerField(default=0)
    pro_active = models.BooleanField(default=False)
    pro_expires_at = models.DateTimeField(null=True, blank=True)
    tier = models.CharField(max_length=10, default='nano')
    tasks_this_period = models.JSONField(default=dict)
    period_reset_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'creator_memberships'

    def __str__(self):
        return f"Membership: {self.creator.username} ({self.total_points} pts)"

    def add_points(self, points):
        self.total_points += points
        self.check_pro_eligibility()
        self.save()

    def check_pro_eligibility(self):
        # points_to_months = {50:1, 100:2, 150:3, 250:6, 400:12}
        milestones = [(50, 1), (100, 2), (150, 3), (250, 6), (400, 12)]

        earned_months = 0
        for points_needed, months in milestones:
            if self.total_points >= points_needed:
                earned_months = months

        if earned_months > 0:
            now = timezone.now()
            current_expiry = self.pro_expires_at or now

            # Extend from whichever is later: now or current expiry
            start_from = max(now, current_expiry)
            new_expiry = start_from + timedelta(days=30 * earned_months)

            self.pro_expires_at = new_expiry
            self.pro_active = True

    def check_pro_status(self):
        if self.pro_expires_at and timezone.now() > self.pro_expires_at:
            self.pro_active = False
            self.save()
        return self.pro_active

    def can_submit_task(self, task_id):
        # Check if already submitted this period
        return task_id not in self.tasks_this_period

    def record_task_submission(self, task_id):
        self.tasks_this_period[task_id] = timezone.now().isoformat()
        self.save()

    def reset_period(self):
        self.tasks_this_period = {}
        # Set next reset date based on tier
        now = timezone.now()
        if self.tier in ['nano', 'micro']:
            # First day of next month
            if now.month == 12:
                next_reset = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_reset = now.replace(month=now.month + 1, day=1)
        else:
            # First day of next quarter
            quarter = (now.month - 1) // 3
            next_quarter_month = ((quarter + 1) * 3) + 1
            if next_quarter_month > 12:
                next_reset = now.replace(year=now.year + 1, month=next_quarter_month - 12, day=1)
            else:
                next_reset = now.replace(month=next_quarter_month, day=1)

        self.period_reset_at = next_reset
        self.save()
