from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        try:
            notification = Notification.objects.get(id=id, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=404)

        notification.mark_read()
        return Response({'message': 'Marked as read'})


class MarkAllNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'message': 'All notifications marked as read'})
