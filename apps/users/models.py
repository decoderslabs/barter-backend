import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'both')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('brand', 'Brand'),
        ('creator', 'Creator'),
        ('both', 'Both'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='creator')
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    bio = models.CharField(max_length=280, blank=True)
    location_city = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    profile_photo_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    barter_score = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.email})"


class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    handle = models.CharField(max_length=100)
    access_token = models.TextField(blank=True)  # encrypted
    refresh_token = models.TextField(blank=True)  # encrypted
    followers = models.PositiveIntegerField(default=0)
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    avg_views = models.PositiveIntegerField(default=0)
    demographics = models.JSONField(default=dict, blank=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'social_accounts'
        unique_together = ['user', 'platform']
        ordering = ['-followers']

    def __str__(self):
        return f"{self.platform}: {self.handle}"

    def set_access_token(self, token):
        if settings.ENCRYPTION_KEY:
            f = Fernet(settings.ENCRYPTION_KEY.encode())
            self.access_token = f.encrypt(token.encode()).decode()
        else:
            self.access_token = token

    def get_access_token(self):
        if settings.ENCRYPTION_KEY and self.access_token:
            try:
                f = Fernet(settings.ENCRYPTION_KEY.encode())
                return f.decrypt(self.access_token.encode()).decode()
            except:
                return self.access_token
        return self.access_token


class BrandProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='brand_profile')
    company_name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    logo_url = models.URLField(blank=True)
    domain_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'brand_profiles'

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


class CreatorProfile(models.Model):
    TIER_CHOICES = [
        ('nano', 'Nano'),
        ('micro', 'Micro'),
        ('mid', 'Mid'),
        ('macro', 'Macro'),
        ('mega', 'Mega'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    niches = models.JSONField(default=list, blank=True)
    content_types = models.JSONField(default=list, blank=True)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='nano')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'creator_profiles'

    def __str__(self):
        return f"{self.user.username} ({self.tier})"

    def calculate_tier(self):
        max_followers = self.user.social_accounts.aggregate(
            max_followers=models.Max('followers')
        )['max_followers'] or 0

        if max_followers >= 1000000:
            self.tier = 'mega'
        elif max_followers >= 500000:
            self.tier = 'macro'
        elif max_followers >= 100000:
            self.tier = 'mid'
        elif max_followers >= 10000:
            self.tier = 'micro'
        else:
            self.tier = 'nano'
        self.save()
