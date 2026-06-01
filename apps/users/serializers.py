from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SocialAccount, BrandProfile, CreatorProfile

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'role', 'name', 'username', 'bio',
                  'location_city', 'location_country']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'name', 'username', 'bio',
                  'location_city', 'location_country', 'profile_photo_url',
                  'is_verified', 'barter_score', 'created_at']
        read_only_fields = ['id', 'barter_score', 'created_at']


class UserMeSerializer(serializers.ModelSerializer):
    brand_profile = serializers.SerializerMethodField()
    creator_profile = serializers.SerializerMethodField()
    social_accounts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'name', 'username', 'bio',
                  'location_city', 'location_country', 'profile_photo_url',
                  'is_verified', 'barter_score', 'brand_profile', 'creator_profile',
                  'social_accounts', 'created_at', 'updated_at']

    def get_brand_profile(self, obj):
        if hasattr(obj, 'brand_profile'):
            return BrandProfileSerializer(obj.brand_profile).data
        return None

    def get_creator_profile(self, obj):
        if hasattr(obj, 'creator_profile'):
            return CreatorProfileSerializer(obj.creator_profile).data
        return None

    def get_social_accounts(self, obj):
        return SocialAccountSerializer(obj.social_accounts.all(), many=True).data


class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = ['id', 'platform', 'handle', 'followers', 'engagement_rate',
                  'avg_views', 'demographics', 'last_synced', 'created_at']


class SocialAccountCreateSerializer(serializers.ModelSerializer):
    access_token = serializers.CharField(write_only=True)
    refresh_token = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = SocialAccount
        fields = ['platform', 'handle', 'access_token', 'refresh_token', 'followers',
                  'engagement_rate', 'avg_views', 'demographics']

    def create(self, validated_data):
        access_token = validated_data.pop('access_token')
        refresh_token = validated_data.pop('refresh_token', '')
        account = SocialAccount(**validated_data)
        account.set_access_token(access_token)
        if refresh_token:
            account.refresh_token = refresh_token
        account.save()
        return account


class BrandProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandProfile
        fields = ['id', 'company_name', 'website', 'industry', 'logo_url', 'domain_verified']


class BrandProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandProfile
        fields = ['company_name', 'website', 'industry']


class CreatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorProfile
        fields = ['id', 'niches', 'content_types', 'tier']


class CreatorProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorProfile
        fields = ['niches', 'content_types']


class CreatorListSerializer(serializers.ModelSerializer):
    creator_profile = CreatorProfileSerializer(read_only=True)
    social_accounts = SocialAccountSerializer(many=True, read_only=True)
    total_followers = serializers.SerializerMethodField()
    avg_engagement_rate = serializers.SerializerMethodField()
    past_collabs = serializers.SerializerMethodField()
    primary_niche = serializers.SerializerMethodField()
    platforms = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'role', 'name', 'username', 'bio',
            'location_city', 'location_country', 'profile_photo_url',
            'is_verified', 'barter_score', 'creator_profile', 'social_accounts',
            'total_followers', 'avg_engagement_rate', 'past_collabs',
            'primary_niche', 'platforms', 'tags', 'created_at',
        ]

    def get_total_followers(self, obj):
        total = sum(account.followers for account in obj.social_accounts.all())
        return total

    def get_avg_engagement_rate(self, obj):
        accounts = obj.social_accounts.all()
        if accounts:
            return sum(account.engagement_rate for account in accounts) / len(accounts)
        return 0.0

    def get_past_collabs(self, obj):
        from apps.deals.models import Deal
        return Deal.objects.filter(creator=obj, status='completed').count()

    def get_primary_niche(self, obj):
        if hasattr(obj, 'creator_profile') and obj.creator_profile.niches:
            return obj.creator_profile.niches[0] if obj.creator_profile.niches else None
        return None

    def get_platforms(self, obj):
        return list(obj.social_accounts.values_list('platform', flat=True))

    def get_tags(self, obj):
        # Mock tags based on niches - in production, this would be a separate field
        if hasattr(obj, 'creator_profile') and obj.creator_profile.niches:
            return [f"{niche} Creator" for niche in obj.creator_profile.niches[:2]]
        return []
