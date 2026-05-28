import uuid
from django.db import models
from django.conf import settings


class DropsCampaign(models.Model):
    GOAL_CHOICES = [
        ('awareness', 'Brand Awareness'),
        ('launch', 'Product Launch'),
        ('event_hype', 'Event Hype'),
        ('review', 'Product Review'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('live', 'Live'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]

    APPROVAL_CHOICES = [
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drops_campaigns')
    offer = models.ForeignKey('offers.Offer', on_delete=models.CASCADE, related_name='drops_campaign')
    name = models.CharField(max_length=100)
    goal = models.CharField(max_length=15, choices=GOAL_CHOICES)
    total_slots = models.PositiveIntegerField()
    filled_slots = models.PositiveIntegerField(default=0)
    approval_mode = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='manual')
    application_deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drops_campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.brand.username})"

    def fill_slot(self):
        if self.filled_slots < self.total_slots:
            self.filled_slots += 1
            if self.filled_slots >= self.total_slots:
                self.status = 'closed'
            self.save()


class DropsApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(DropsCampaign, on_delete=models.CASCADE, related_name='applications')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drops_applications')
    pitch = models.TextField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    deal = models.ForeignKey('deals.Deal', on_delete=models.SET_NULL, null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'drops_applications'
        ordering = ['-applied_at']
        unique_together = ['campaign', 'creator']

    def __str__(self):
        return f"Application by {self.creator.username} for {self.campaign.name}"
