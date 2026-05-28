import uuid
from django.db import models
from django.conf import settings


class Offer(models.Model):
    TYPE_CHOICES = [
        ('saas', 'SaaS'),
        ('physical', 'Physical Product'),
        ('event_pass', 'Event Pass'),
        ('experience', 'Experience'),
        ('merchandise', 'Merchandise'),
        ('course', 'Course'),
        ('gift_card', 'Gift Card'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('live', 'Live'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]

    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('AED', 'UAE Dirham'),
        ('USD', 'US Dollar'),
    ]

    RIGHTS_CHOICES = [
        ('none', 'None'),
        ('standard', 'Standard'),
        ('extended', 'Extended'),
        ('buyout', 'Buyout'),
    ]

    EXCLUSIVITY_CHOICES = [
        ('none', 'None'),
        ('category_30', 'Category 30 Days'),
        ('full_60', 'Full 60 Days'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=80)
    description = models.TextField(max_length=500)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    quantity = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    content_ask = models.JSONField(default=dict)  # {types[], platforms[], count}
    kpi_preferences = models.JSONField(default=dict)  # {min_followers, min_engagement, niches[]}
    rights_tier = models.CharField(max_length=10, choices=RIGHTS_CHOICES, default='none')
    raw_files_required = models.BooleanField(default=False)
    exclusivity = models.CharField(max_length=15, choices=EXCLUSIVITY_CHOICES, default='none')
    images = models.JSONField(default=list, blank=True)  # list of URLs
    attachments = models.JSONField(default=list, blank=True)
    proposal_deadline = models.DateTimeField(null=True, blank=True)
    max_proposals = models.PositiveIntegerField(null=True, blank=True)
    shipping_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'offers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.brand.username})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.quantity_remaining = self.quantity
        super().save(*args, **kwargs)

    def decrement_quantity(self):
        if self.quantity_remaining > 0:
            self.quantity_remaining -= 1
            if self.quantity_remaining == 0:
                self.status = 'closed'
            self.save()

    def increment_quantity(self):
        if self.quantity_remaining < self.quantity:
            self.quantity_remaining += 1
            self.save()

    def get_proposal_count(self):
        from apps.proposals.models import Proposal
        return Proposal.objects.filter(offer=self).count()

    def is_drops(self):
        from apps.drops.models import DropsCampaign
        return DropsCampaign.objects.filter(offer=self).exists()
