import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Proposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('countered', 'Countered'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.ForeignKey('offers.Offer', on_delete=models.CASCADE, related_name='proposals')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals')
    pitch = models.TextField(max_length=500)
    deliverables = models.JSONField(default=dict)  # {types[], platforms[], count, details}
    timeline = models.DateField()
    round_number = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    counter_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='countered_proposals')
    deal = models.OneToOneField('deals.Deal', on_delete=models.SET_NULL, null=True, blank=True, related_name='proposal_link')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'proposals'
        ordering = ['-created_at']
        unique_together = ['offer', 'creator']

    def __str__(self):
        return f"Proposal by {self.creator.username} for {self.offer.title}"

    def save(self, *args, **kwargs):
        if self.round_number >= 3 and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def can_counter(self):
        return self.round_number < 3 and self.status in ['pending', 'countered']

    def counter(self, user, deliverables, timeline, note):
        if not self.can_counter():
            raise ValueError("Cannot counter this proposal")

        self.round_number += 1
        self.counter_by = user
        self.deliverables = deliverables
        self.timeline = timeline
        self.status = 'countered'

        ProposalCounter.objects.create(
            proposal=self,
            sent_by=user,
            deliverables=deliverables,
            timeline=timeline,
            note=note,
            round_number=self.round_number
        )
        self.save()

    def accept(self):
        if self.status not in ['pending', 'countered']:
            raise ValueError("Cannot accept proposal in current state")
        self.status = 'accepted'
        self.save()

        from apps.deals.models import Deal
        Deal.objects.create_from_proposal(self)

    def decline(self):
        if self.status not in ['pending', 'countered']:
            raise ValueError("Cannot decline proposal in current state")
        self.status = 'declined'
        self.save()

    def expire(self):
        if self.status == 'countered' and self.round_number >= 3:
            if self.expires_at and timezone.now() > self.expires_at:
                self.status = 'expired'
                self.save()


class ProposalCounter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='counters')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    deliverables = models.JSONField(default=dict)
    timeline = models.DateField()
    note = models.TextField(max_length=300, blank=True)
    round_number = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proposal_counters'
        ordering = ['created_at']

    def __str__(self):
        return f"Counter round {self.round_number} on {self.proposal.id}"
