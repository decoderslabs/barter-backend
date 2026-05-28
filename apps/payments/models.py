import uuid
from django.db import models
from django.conf import settings


class Payment(models.Model):
    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    deal = models.ForeignKey('deals.Deal', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    gateway = models.CharField(max_length=10, choices=GATEWAY_CHOICES)
    gateway_ref = models.CharField(max_length=200)  # razorpay order_id or stripe payment_intent_id
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    invoice_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment: {self.amount} {self.currency} ({self.status})"


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('scale', 'Scale'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
    ]

    GATEWAY_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='free')
    gateway = models.CharField(max_length=10, choices=GATEWAY_CHOICES)
    gateway_sub_id = models.CharField(max_length=200)  # subscription ID from gateway
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    current_period_end = models.DateTimeField()
    deals_used = models.PositiveIntegerField(default=0)
    deals_included = models.PositiveIntegerField(default=5)  # Default 5 deals for starter
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Subscription: {self.brand.username} - {self.plan}"

    def can_create_deal(self):
        if self.plan == 'free':
            return False
        return self.deals_used < self.deals_included

    def increment_deals_used(self):
        self.deals_used += 1
        self.save()

    def reset_deals_used(self):
        self.deals_used = 0
        self.save()


class Wallet(models.Model):
    TRANSACTION_TYPES = [
        ('earn', 'Earn'),
        ('spend', 'Spend'),
        ('transfer', 'Transfer'),
        ('refund', 'Refund'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.PositiveIntegerField(default=0)
    lifetime_earned = models.PositiveIntegerField(default=0)
    lifetime_spent = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self):
        return f"Wallet: {self.user.username} ({self.balance} pts)"

    def add_points(self, amount, description="", source=None):
        """Add points to wallet"""
        self.balance += amount
        self.lifetime_earned += amount
        self.save()

        WalletTransaction.objects.create(
            wallet=self,
            type='earn',
            amount=amount,
            description=description,
            source=source
        )
        return self.balance

    def spend_points(self, amount, description="", source=None):
        """Spend points from wallet"""
        if self.balance < amount:
            raise ValueError("Insufficient points")

        self.balance -= amount
        self.lifetime_spent += amount
        self.save()

        WalletTransaction.objects.create(
            wallet=self,
            type='spend',
            amount=-amount,
            description=description,
            source=source
        )
        return self.balance

    def transfer_points(self, to_user, amount, description=""):
        """Transfer points to another user"""
        if self.balance < amount:
            raise ValueError("Insufficient points")

        # Deduct from sender
        self.spend_points(amount, description=f"Transfer to {to_user.username}: {description}")

        # Add to recipient
        to_wallet, _ = Wallet.objects.get_or_create(user=to_user)
        to_wallet.add_points(amount, description=f"Transfer from {self.user.username}: {description}")

        return self.balance


class WalletTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=Wallet.TRANSACTION_TYPES)
    amount = models.IntegerField()  # Positive for earn, negative for spend
    description = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=100, blank=True)  # task_id, deal_id, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.username}: {self.type} {self.amount}"
