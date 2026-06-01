from rest_framework import serializers
from .models import Offer


class OfferSerializer(serializers.ModelSerializer):
    brand_username = serializers.CharField(source='brand.username', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    brand_company_name = serializers.SerializerMethodField()
    proposal_count = serializers.SerializerMethodField()
    is_drops = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'brand', 'brand_username', 'brand_name', 'brand_company_name',
            'type', 'title', 'description', 'estimated_value', 'currency',
            'quantity', 'quantity_remaining', 'status', 'content_ask',
            'kpi_preferences', 'rights_tier', 'raw_files_required',
            'exclusivity', 'images', 'attachments', 'proposal_deadline',
            'max_proposals', 'shipping_required', 'proposal_count',
            'is_drops', 'created_at', 'updated_at'
        ]
        read_only_fields = ['brand', 'quantity_remaining']

    def get_brand_company_name(self, obj):
        if hasattr(obj.brand, 'brand_profile'):
            return obj.brand.brand_profile.company_name
        return None

    def get_proposal_count(self, obj):
        return obj.get_proposal_count()

    def get_is_drops(self, obj):
        return obj.is_drops()


class OfferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = [
            'type', 'title', 'description', 'estimated_value', 'currency',
            'quantity', 'status', 'content_ask', 'kpi_preferences',
            'rights_tier', 'raw_files_required', 'exclusivity',
            'images', 'attachments', 'proposal_deadline',
            'max_proposals', 'shipping_required'
        ]

    def validate(self, data):
        if data.get('quantity', 0) < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        if data.get('estimated_value', 0) <= 0:
            raise serializers.ValidationError("Estimated value must be greater than 0")
        return data


class OfferUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'estimated_value', 'currency',
            'status', 'content_ask', 'kpi_preferences', 'rights_tier',
            'raw_files_required', 'exclusivity', 'images', 'attachments',
            'proposal_deadline', 'max_proposals', 'shipping_required'
        ]


class OfferListSerializer(serializers.ModelSerializer):
    brand_username = serializers.CharField(source='brand.username', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    brand_logo_url = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    is_drops = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'brand_username', 'brand_name', 'brand_logo_url', 'type', 'title',
            'estimated_value', 'currency', 'quantity_remaining',
            'status', 'content_ask', 'match_score', 'is_drops', 'created_at'
        ]

    def get_brand_logo_url(self, obj):
        if hasattr(obj.brand, 'brand_profile') and obj.brand.brand_profile.logo_url:
            return obj.brand.brand_profile.logo_url
        return None

    def get_match_score(self, obj):
        # Mock match score (0-100) - in production, this would be computed based on
        # creator's profile alignment with offer requirements
        import random
        return random.randint(60, 95)

    def get_is_drops(self, obj):
        return obj.is_drops()


class ValueEngineSerializer(serializers.Serializer):
    offer_id = serializers.UUIDField()
    estimated_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    recommended_content_types = serializers.ListField(child=serializers.CharField())
    recommended_platforms = serializers.ListField(child=serializers.CharField())
    recommended_post_count = serializers.IntegerField()
    estimated_engagement = serializers.IntegerField()
    similar_offers_count = serializers.IntegerField()
