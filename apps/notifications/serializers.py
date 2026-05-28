from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'body', 'deep_link', 'read', 'created_at']


class NotificationMarkReadSerializer(serializers.Serializer):
    pass
