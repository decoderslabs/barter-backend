from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import Deal, Delivery, DealMessage, RevisionRequest
from .serializers import (
    DealSerializer, DealListSerializer, DealMessageSerializer,
    DealMessageCreateSerializer, ShipDealSerializer, DeliverDealSerializer,
    RevisionRequestSerializer
)
from apps.notifications.utils import send_notification


class IsDealParty(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in [obj.brand, obj.creator]


class IsBrand(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['brand', 'both']


class IsCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['creator', 'both']


class DealListView(generics.ListAPIView):
    serializer_class = DealListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Deal.objects.filter(
            Q(brand=user) | Q(creator=user)
        ).select_related('offer', 'brand', 'creator').order_by('-created_at')


class DealDetailView(generics.RetrieveAPIView):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated, IsDealParty]


class ShipDealView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if deal.brand != request.user:
            return Response({'error': 'Only brand can ship'}, status=403)

        serializer = ShipDealSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        deal.set_shipping_address(serializer.validated_data['shipping_address'])
        deal.ship()
        deal.save()

        send_notification(
            user_id=deal.creator.id,
            notification_type='brand_shipped',
            title='Item Shipped',
            body=f'{deal.brand.name} has shipped your item for {deal.offer.title}',
            deep_link=f'/deals/{deal.id}'
        )

        return Response({'message': 'Item marked as shipped'})


class ConfirmReceiptView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if deal.creator != request.user:
            return Response({'error': 'Only creator can confirm receipt'}, status=403)

        deal.confirm_receipt()

        send_notification(
            user_id=deal.brand.id,
            notification_type='creator_confirmed',
            title='Receipt Confirmed',
            body=f'{deal.creator.name} confirmed receipt of the item',
            deep_link=f'/deals/{deal.id}'
        )

        return Response({'message': 'Receipt confirmed'})


class DeliverContentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if deal.creator != request.user:
            return Response({'error': 'Only creator can deliver content'}, status=403)

        serializer = DeliverDealSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        deal.deliver(
            files=serializer.validated_data['files'],
            post_urls=serializer.validated_data['post_urls'],
            notes=serializer.validated_data.get('notes', '')
        )

        send_notification(
            user_id=deal.brand.id,
            notification_type='content_delivered',
            title='Content Delivered',
            body=f'{deal.creator.name} has submitted content for {deal.offer.title}',
            deep_link=f'/deals/{deal.id}'
        )

        return Response({'message': 'Content delivered successfully'})


class ApproveDeliveryView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if deal.brand != request.user:
            return Response({'error': 'Only brand can approve'}, status=403)

        if deal.status != 'delivered':
            return Response({'error': 'No content to approve'}, status=400)

        deal.approve_delivery()

        # Create ratings for both parties
        from apps.ratings.models import Rating
        Rating.objects.create(
            deal=deal,
            rater=deal.brand,
            ratee=deal.creator,
            stars=0  # pending
        )
        Rating.objects.create(
            deal=deal,
            rater=deal.creator,
            ratee=deal.brand,
            stars=0  # pending
        )

        send_notification(
            user_id=deal.creator.id,
            notification_type='deal_complete',
            title='Deal Complete!',
            body=f'{deal.offer.title} has been marked complete. Please rate your experience.',
            deep_link=f'/deals/{deal.id}/rate'
        )

        return Response({'message': 'Content approved, deal complete'})


class RequestRevisionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if deal.brand != request.user:
            return Response({'error': 'Only brand can request revisions'}, status=403)

        serializer = RevisionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            deal.request_revision(serializer.validated_data['reason'])
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        send_notification(
            user_id=deal.creator.id,
            notification_type='revision_requested',
            title='Revision Requested',
            body=f'{deal.brand.name} has requested a revision for {deal.offer.title}',
            deep_link=f'/deals/{deal.id}'
        )

        return Response({'message': 'Revision requested'})


class CompleteDealView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDealParty]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if request.user not in [deal.brand, deal.creator]:
            return Response({'error': 'Access denied'}, status=403)

        deal.complete()

        return Response({'message': 'Deal marked as complete'})


class DisputeDealView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDealParty]

    def post(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if request.user not in [deal.brand, deal.creator]:
            return Response({'error': 'Access denied'}, status=403)

        deal.dispute()

        # Notify both parties
        other_party = deal.creator if request.user == deal.brand else deal.brand
        send_notification(
            user_id=other_party.id,
            notification_type='deal_disputed',
            title='Deal Disputed',
            body='A dispute has been raised for this deal. Admin will review.',
            deep_link=f'/deals/{deal.id}'
        )

        return Response({'message': 'Deal marked as disputed, admin notified'})


class DealMessageListView(generics.ListAPIView):
    serializer_class = DealMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        deal_id = self.kwargs.get('id')
        return DealMessage.objects.filter(deal_id=deal_id).order_by('created_at')

    def check_permissions(self, request):
        super().check_permissions(request)
        try:
            deal = Deal.objects.get(id=self.kwargs.get('id'))
            if request.user not in [deal.brand, deal.creator]:
                self.permission_denied(request, message="Access denied to deal messages")
        except Deal.DoesNotExist:
            pass


class DealMessageCreateView(generics.CreateAPIView):
    serializer_class = DealMessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealParty]

    def perform_create(self, serializer):
        deal_id = self.kwargs.get('id')
        deal = Deal.objects.get(id=deal_id)
        message = serializer.save(deal=deal, sender=self.request.user)

        # Notify other party
        recipient = deal.creator if self.request.user == deal.brand else deal.brand
        send_notification(
            user_id=recipient.id,
            notification_type='deal_message',
            title='New Message',
            body=f'New message in {deal.offer.title} deal room',
            deep_link=f'/deals/{deal.id}/messages'
        )

        return message
