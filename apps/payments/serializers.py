from rest_framework import serializers
from .models import Payment, Subscription


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'deal', 'amount', 'currency', 'gateway',
            'gateway_ref', 'status', 'invoice_url', 'created_at'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    deal_id = serializers.UUIDField()
    gateway = serializers.ChoiceField(choices=['razorpay', 'stripe'])


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'gateway', 'status', 'current_period_end',
            'deals_used', 'deals_included', 'created_at'
        ]


class SubscriptionCreateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=['starter', 'growth', 'scale'])
    gateway = serializers.ChoiceField(choices=['razorpay', 'stripe'])
