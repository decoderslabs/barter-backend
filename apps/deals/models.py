import uuid
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet


class DealManager(models.Manager):
    def create_from_proposal(self, proposal):
        agreed_terms = {
            'offer_title': proposal.offer.title,
            'offer_type': proposal.offer.type,
            'offer_estimated_value': str(proposal.offer.estimated_value),
            'creator_deliverables': proposal.deliverables,
            'timeline': str(proposal.timeline),
            'rights_tier': proposal.offer.rights_tier,
            'raw_files_required': proposal.offer.raw_files_required,
            'exclusivity': proposal.offer.exclusivity,
        }

        # Calculate deal fee
        value = proposal.offer.estimated_value
        currency = proposal.offer.currency

        if currency == 'INR':
            if value <= 5000:
                fee = 999
            elif value <= 15000:
                fee = 1499
            elif value <= 50000:
                fee = 1999
            else:
                fee = 2999
        elif currency == 'AED':
            # 1 INR ≈ 0.044 AED
            if value <= 5000:
                fee = round(999 * 0.044)
            elif value <= 15000:
                fee = round(1499 * 0.044)
            elif value <= 50000:
                fee = round(1999 * 0.044)
            else:
                fee = round(2999 * 0.044)
        else:  # USD - 1 INR ≈ 0.012 USD
            if value <= 5000:
                fee = round(999 * 0.012, 2)
            elif value <= 15000:
                fee = round(1499 * 0.012, 2)
            elif value <= 50000:
                fee = round(1999 * 0.012, 2)
            else:
                fee = round(2999 * 0.012, 2)

        # Check creator Pro status
        from apps.membership.models import CreatorMembership
        try:
            membership = proposal.creator.membership
            is_pro = membership.pro_active and (membership.pro_expires_at is None or membership.pro_expires_at > timezone.now())
        except CreatorMembership.DoesNotExist:
            is_pro = False

        deal = self.create(
            offer=proposal.offer,
            proposal=proposal,
            brand=proposal.offer.brand,
            creator=proposal.creator,
            agreed_terms=agreed_terms,
            rights_tier=proposal.offer.rights_tier,
            raw_files_required=proposal.offer.raw_files_required,
            exclusivity=proposal.offer.exclusivity,
            deal_fee=fee,
            currency=currency,
            status='active' if is_pro else 'pending_membership',
            deadline=proposal.timeline,
        )

        # Link deal back to proposal
        proposal.deal = deal
        proposal.save()

        return deal


class Deal(models.Model):
    STATUS_CHOICES = [
        ('pending_membership', 'Pending Membership'),
        ('active', 'Active'),
        ('delivered', 'Delivered'),
        ('revision_requested', 'Revision Requested'),
        ('complete', 'Complete'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.ForeignKey('offers.Offer', on_delete=models.CASCADE, related_name='deals')
    proposal = models.OneToOneField('proposals.Proposal', on_delete=models.CASCADE, related_name='accepted_deal')
    brand = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='brand_deals')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='creator_deals')
    agreed_terms = models.JSONField(default=dict)
    rights_tier = models.CharField(max_length=20)
    raw_files_required = models.BooleanField(default=False)
    exclusivity = models.CharField(max_length=20)
    deal_fee = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_membership')
    shipping_address = models.TextField(blank=True)  # encrypted JSON
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateField()
    contract_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DealManager()

    class Meta:
        db_table = 'deals'
        ordering = ['-created_at']

    def __str__(self):
        return f"Deal: {self.offer.title} ({self.brand.username} <> {self.creator.username})"

    def set_shipping_address(self, address_dict):
        if settings.ENCRYPTION_KEY:
            f = Fernet(settings.ENCRYPTION_KEY.encode())
            self.shipping_address = f.encrypt(str(address_dict).encode()).decode()
        else:
            self.shipping_address = str(address_dict)

    def get_shipping_address(self):
        if settings.ENCRYPTION_KEY and self.shipping_address:
            try:
                f = Fernet(settings.ENCRYPTION_KEY.encode())
                return eval(f.decrypt(self.shipping_address.encode()).decode())
            except:
                return eval(self.shipping_address) if self.shipping_address else None
        return eval(self.shipping_address) if self.shipping_address else None

    def ship(self):
        if self.status == 'active':
            self.shipped_at = timezone.now()
            self.save()

    def confirm_receipt(self):
        if self.status == 'active' and self.shipped_at:
            pass  # Just confirmation

    def deliver(self, files, post_urls, notes):
        if self.status in ['active', 'revision_requested']:
            Delivery.objects.create(
                deal=self,
                files=files,
                post_urls=post_urls,
                notes=notes,
                status='pending'
            )
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save()

    def approve_delivery(self):
        if self.status == 'delivered':
            self.status = 'complete'
            self.completed_at = timezone.now()
            self.save()

    def request_revision(self, reason):
        if self.status == 'delivered':
            revision_count = RevisionRequest.objects.filter(deal=self).count()
            if revision_count < 2:
                RevisionRequest.objects.create(
                    deal=self,
                    requested_by=self.brand,
                    reason=reason,
                    round_number=revision_count + 1
                )
                self.status = 'revision_requested'
                self.save()
            else:
                raise ValueError("Maximum 2 revisions allowed")

    def complete(self):
        if self.status in ['delivered', 'revision_requested']:
            self.status = 'complete'
            self.completed_at = timezone.now()
            self.save()

    def dispute(self):
        if self.status in ['active', 'delivered', 'revision_requested']:
            self.status = 'disputed'
            self.save()


class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('revision', 'Revision'),
        ('disputed', 'Disputed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='deliveries')
    files = models.JSONField(default=list)  # Supabase URLs
    post_urls = models.JSONField(default=list)  # live post links
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'deliveries'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Delivery for Deal {self.deal.id}"


class DealMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    attachment_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'deal_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message in Deal {self.deal.id} by {self.sender.username}"

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save()


class RevisionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='revisions')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=300)
    round_number = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'revision_requests'
        ordering = ['created_at']

    def __str__(self):
        return f"Revision {self.round_number} for Deal {self.deal.id}"


from django.utils import timezone
