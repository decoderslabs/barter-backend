from rest_framework import serializers


class DealsAnalyticsSerializer(serializers.Serializer):
    total_deals = serializers.IntegerField()
    active_deals = serializers.IntegerField()
    completed_deals = serializers.IntegerField()
    disputed_deals = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_deal_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    deals_by_status = serializers.ListField()
    recent_deals_30_days = serializers.IntegerField()
    deals_over_time = serializers.ListField()


class CreatorsAnalyticsSerializer(serializers.Serializer):
    top_creators = serializers.ListField()
    creator_tiers = serializers.ListField()
    avg_creator_barter_score = serializers.FloatField()


class ContentAnalyticsSerializer(serializers.Serializer):
    content_types = serializers.DictField()
    platforms = serializers.DictField()
    avg_delivery_days = serializers.IntegerField()
