from rest_framework import serializers
from django.utils import timezone
from .models import Proposal, ProposalCounter
from apps.users.serializers import UserSerializer


class ProposalCounterSerializer(serializers.ModelSerializer):
    sent_by_username = serializers.CharField(source='sent_by.username', read_only=True)

    class Meta:
        model = ProposalCounter
        fields = ['id', 'sent_by', 'sent_by_username', 'deliverables', 'timeline',
                  'note', 'round_number', 'created_at']


class ProposalSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    offer_title = serializers.CharField(source='offer.title', read_only=True)
    offer_brand_username = serializers.CharField(source='offer.brand.username', read_only=True)
    counters = ProposalCounterSerializer(many=True, read_only=True)
    can_counter = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            'id', 'offer', 'offer_title', 'offer_brand_username',
            'creator', 'creator_username', 'creator_name',
            'pitch', 'deliverables', 'timeline', 'round_number',
            'status', 'counter_by', 'can_counter', 'counters',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['round_number', 'status', 'counter_by']

    def get_can_counter(self, obj):
        return obj.can_counter()


class ProposalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proposal
        fields = ['offer', 'pitch', 'deliverables', 'timeline']

    def validate_offer(self, value):
        if value.status != 'live':
            raise serializers.ValidationError("This offer is not accepting proposals")
        if value.quantity_remaining <= 0:
            raise serializers.ValidationError("No slots remaining for this offer")
        return value

    def validate(self, data):
        user = self.context['request'].user
        offer = data['offer']

        if offer.brand == user:
            raise serializers.ValidationError("Cannot propose on your own offer")

        if user.role not in ['creator', 'both']:
            raise serializers.ValidationError("Only creators can submit proposals")

        # Check if max proposals reached
        if offer.max_proposals:
            current_count = Proposal.objects.filter(offer=offer).count()
            if current_count >= offer.max_proposals:
                raise serializers.ValidationError("Maximum proposals reached for this offer")

        # Check deadline
        if offer.proposal_deadline and offer.proposal_deadline < timezone.now():
            raise serializers.ValidationError("Proposal deadline has passed")

        return data

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class ProposalListSerializer(serializers.ModelSerializer):
    offer_title = serializers.CharField(source='offer.title', read_only=True)
    offer_brand_username = serializers.CharField(source='offer.brand.username', read_only=True)
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    pitch = serializers.CharField(read_only=True)
    deliverables = serializers.JSONField(read_only=True)
    timeline = serializers.DateField(read_only=True)
    can_counter = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            'id', 'offer_title', 'offer_brand_username',
            'creator_username', 'creator_name', 'status', 'round_number',
            'pitch', 'deliverables', 'timeline', 'can_counter', 'created_at'
        ]

    def get_can_counter(self, obj):
        return obj.can_counter()


class CounterProposalSerializer(serializers.Serializer):
    deliverables = serializers.JSONField()
    timeline = serializers.DateField()
    note = serializers.CharField(max_length=300, required=False, allow_blank=True)


class AcceptProposalSerializer(serializers.Serializer):
    pass


class DeclineProposalSerializer(serializers.Serializer):
    pass
