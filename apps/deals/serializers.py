from rest_framework import serializers
from .models import Deal, Delivery, DealMessage, RevisionRequest


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'files', 'post_urls', 'notes', 'submitted_at', 'status']


class RevisionRequestSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)

    class Meta:
        model = RevisionRequest
        fields = ['id', 'requested_by', 'requested_by_username', 'reason', 'round_number', 'created_at']


class DealMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_name = serializers.CharField(source='sender.name', read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = DealMessage
        fields = ['id', 'sender', 'sender_username', 'sender_name', 'body',
                  'attachment_url', 'created_at', 'read_at', 'is_read']

    def get_is_read(self, obj):
        return obj.read_at is not None


class DealMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealMessage
        fields = ['body', 'attachment_url']


class DealSerializer(serializers.ModelSerializer):
    brand_username = serializers.CharField(source='brand.username', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    offer_title = serializers.CharField(source='offer.title', read_only=True)
    offer_type = serializers.CharField(source='offer.type', read_only=True)
    shipping_address = serializers.SerializerMethodField()
    latest_delivery = serializers.SerializerMethodField()
    revisions = RevisionRequestSerializer(many=True, read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'offer', 'offer_title', 'offer_type',
            'brand', 'brand_username', 'brand_name',
            'creator', 'creator_username', 'creator_name',
            'agreed_terms', 'rights_tier', 'raw_files_required',
            'exclusivity', 'deal_fee', 'currency', 'status',
            'shipping_address', 'shipped_at', 'delivered_at',
            'completed_at', 'deadline', 'contract_url',
            'latest_delivery', 'revisions', 'created_at', 'updated_at'
        ]

    def get_shipping_address(self, obj):
        # Only show to deal parties
        request = self.context.get('request')
        if request and request.user:
            if request.user in [obj.brand, obj.creator]:
                return obj.get_shipping_address()
        return None

    def get_latest_delivery(self, obj):
        latest = obj.deliveries.first()
        if latest:
            return DeliverySerializer(latest).data
        return None


class DealListSerializer(serializers.ModelSerializer):
    brand_username = serializers.CharField(source='brand.username', read_only=True)
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    offer_title = serializers.CharField(source='offer.title', read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'offer_title', 'brand_username', 'creator_username',
            'status', 'deal_fee', 'currency', 'deadline', 'created_at'
        ]


class ShipDealSerializer(serializers.Serializer):
    shipping_address = serializers.JSONField()


class DeliverDealSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.URLField())
    post_urls = serializers.ListField(child=serializers.URLField())
    notes = serializers.CharField(required=False, allow_blank=True)


class RevisionRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300)
