from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Rating
from .serializers import RatingSerializer, RatingCreateSerializer


class IsDealParty(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in [obj.deal.brand, obj.deal.creator]


class RateDealView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        from apps.deals.models import Deal
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if request.user not in [deal.brand, deal.creator]:
            return Response({'error': 'Access denied'}, status=403)

        if deal.status != 'complete':
            return Response({'error': 'Can only rate completed deals'}, status=400)

        serializer = RatingCreateSerializer(
            data=request.data,
            context={'request': request, 'deal': deal}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        rating = serializer.save()

        # Notify other party
        other_party = deal.creator if request.user == deal.brand else deal.brand
        send_notification(
            user_id=other_party.id,
            notification_type='rating_received',
            title='New Rating',
            body=f'You received a {rating.stars}-star rating',
            deep_link=f'/deals/{deal.id}'
        )

        return Response(RatingSerializer(rating).data)


class UserRatingsListView(generics.ListAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get('id')
        return Rating.objects.filter(
            ratee_id=user_id,
            published_at__isnull=False
        ).select_related('rater', 'ratee', 'deal').order_by('-published_at')


from apps.notifications.utils import send_notification
