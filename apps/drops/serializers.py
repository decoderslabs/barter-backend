from rest_framework import serializers
from .models import DropsCampaign, DropsApplication


class DropsCampaignSerializer(serializers.ModelSerializer):
    brand_username = serializers.CharField(source='brand.username', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = DropsCampaign
        fields = [
            'id', 'brand', 'brand_username', 'brand_name',
            'offer', 'name', 'goal', 'total_slots', 'filled_slots',
            'approval_mode', 'application_deadline', 'status',
            'application_count', 'created_at'
        ]

    def get_application_count(self, obj):
        return obj.applications.count()


class DropsCampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DropsCampaign
        fields = ['offer', 'name', 'goal', 'total_slots', 'approval_mode', 'application_deadline']


class DropsApplicationSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)

    class Meta:
        model = DropsApplication
        fields = [
            'id', 'campaign', 'campaign_name', 'creator', 'creator_username',
            'creator_name', 'pitch', 'status', 'deal', 'applied_at', 'reviewed_at'
        ]


class DropsApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DropsApplication
        fields = ['campaign', 'pitch']

    def validate_campaign(self, value):
        if value.status != 'live':
            raise serializers.ValidationError("This campaign is not accepting applications")
        if value.filled_slots >= value.total_slots:
            raise serializers.ValidationError("No slots remaining")
        if value.application_deadline and value.application_deadline < timezone.now():
            raise serializers.ValidationError("Application deadline has passed")
        return value

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
