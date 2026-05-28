from rest_framework import serializers
from .models import Rating


class RatingSerializer(serializers.ModelSerializer):
    rater_username = serializers.CharField(source='rater.username', read_only=True)
    rater_name = serializers.CharField(source='rater.name', read_only=True)
    ratee_username = serializers.CharField(source='ratee.username', read_only=True)
    ratee_name = serializers.CharField(source='ratee.name', read_only=True)
    is_published = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = [
            'id', 'deal', 'rater', 'rater_username', 'rater_name',
            'ratee', 'ratee_username', 'ratee_name', 'stars',
            'review_text', 'is_published', 'published_at', 'created_at'
        ]

    def get_is_published(self, obj):
        return obj.published_at is not None


class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['stars', 'review_text']

    def validate_stars(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5 stars")
        return value

    def create(self, validated_data):
        deal = self.context['deal']
        rater = self.context['request'].user

        # Determine ratee
        ratee = deal.creator if rater == deal.brand else deal.brand

        rating, created = Rating.objects.update_or_create(
            deal=deal,
            rater=rater,
            defaults={
                'ratee': ratee,
                'stars': validated_data['stars'],
                'review_text': validated_data.get('review_text', '')
            }
        )

        rating.publish()

        return rating
