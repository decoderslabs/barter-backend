import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('proposal_received', 'Proposal Received'),
        ('proposal_accepted', 'Proposal Accepted'),
        ('proposal_countered', 'Proposal Countered'),
        ('proposal_declined', 'Proposal Declined'),
        ('deal_room_created', 'Deal Room Created'),
        ('brand_shipped', 'Brand Shipped'),
        ('creator_confirmed', 'Creator Confirmed'),
        ('content_delivered', 'Content Delivered'),
        ('revision_requested', 'Revision Requested'),
        ('deal_complete', 'Deal Complete'),
        ('rating_received', 'Rating Received'),
        ('membership_submitted', 'Membership Submitted'),
        ('membership_approved', 'Membership Approved'),
        ('membership_rejected', 'Membership Rejected'),
        ('pro_expiring', 'Pro Expiring'),
        ('drops_application', 'Drops Application'),
        ('drops_approved', 'Drops Approved'),
        ('deal_message', 'Deal Message'),
        ('deal_disputed', 'Deal Disputed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    body = models.TextField()
    deep_link = models.URLField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_read(self):
        if not self.read:
            self.read = True
            self.save()
