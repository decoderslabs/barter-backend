from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from .models import Proposal
from .serializers import (
    ProposalSerializer, ProposalCreateSerializer, ProposalListSerializer,
    CounterProposalSerializer, AcceptProposalSerializer, DeclineProposalSerializer
)
from apps.notifications.utils import send_notification


class IsCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['creator', 'both']


class IsBrand(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['brand', 'both']


class ProposalCreateView(generics.CreateAPIView):
    serializer_class = ProposalCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def perform_create(self, serializer):
        proposal = serializer.save()

        # Send notification to brand
        send_notification(
            user_id=proposal.offer.brand.id,
            notification_type='proposal_received',
            title='New Proposal Received',
            body=f'{proposal.creator.name} sent a proposal for {proposal.offer.title}',
            deep_link=f'/offers/{proposal.offer.id}/proposals/{proposal.id}'
        )

        return proposal


class ProposalListView(generics.ListAPIView):
    serializer_class = ProposalListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'brand':
            return Proposal.objects.filter(offer__brand=user)
        elif user.role == 'creator':
            return Proposal.objects.filter(creator=user)
        else:  # both
            return Proposal.objects.filter(
                models.Q(offer__brand=user) | models.Q(creator=user)
            ).distinct()


class ProposalDetailView(generics.RetrieveAPIView):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        user = request.user
        is_brand = obj.offer.brand == user
        is_creator = obj.creator == user
        if not (is_brand or is_creator):
            self.permission_denied(request, message="You don't have access to this proposal")


class CounterProposalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            proposal = Proposal.objects.get(id=id)
        except Proposal.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=404)

        # Check permissions
        user = request.user
        is_brand = proposal.offer.brand == user
        is_creator = proposal.creator == user

        if not (is_brand or is_creator):
            return Response({'error': 'Access denied'}, status=403)

        if not proposal.can_counter():
            return Response({'error': 'Cannot counter this proposal (max 3 rounds)'}, status=400)

        serializer = CounterProposalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            proposal.counter(
                user=user,
                deliverables=serializer.validated_data['deliverables'],
                timeline=serializer.validated_data['timeline'],
                note=serializer.validated_data.get('note', '')
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Send notification to other party
        recipient = proposal.creator if is_brand else proposal.offer.brand
        send_notification(
            user_id=recipient.id,
            notification_type='proposal_countered',
            title='Proposal Countered',
            body=f'Your proposal for {proposal.offer.title} has been countered (Round {proposal.round_number})',
            deep_link=f'/proposals/{proposal.id}'
        )

        return Response(ProposalSerializer(proposal).data)


class AcceptProposalView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id):
        try:
            proposal = Proposal.objects.get(id=id)
        except Proposal.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=404)

        if proposal.offer.brand != request.user:
            return Response({'error': 'Only the brand owner can accept proposals'}, status=403)

        if proposal.status not in ['pending', 'countered']:
            return Response({'error': 'Cannot accept proposal in current state'}, status=400)

        try:
            proposal.accept()
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Decrement offer quantity
        proposal.offer.decrement_quantity()

        # Send notification to creator
        send_notification(
            user_id=proposal.creator.id,
            notification_type='proposal_accepted',
            title='Proposal Accepted!',
            body=f'Your proposal for {proposal.offer.title} has been accepted',
            deep_link=f'/deals/{proposal.deal.id}'
        )

        return Response({
            'message': 'Proposal accepted successfully',
            'deal_id': str(proposal.deal.id)
        })


class DeclineProposalView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id):
        try:
            proposal = Proposal.objects.get(id=id)
        except Proposal.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=404)

        if proposal.offer.brand != request.user:
            return Response({'error': 'Only the brand owner can decline proposals'}, status=403)

        if proposal.status not in ['pending', 'countered']:
            return Response({'error': 'Cannot decline proposal in current state'}, status=400)

        try:
            proposal.decline()
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Send notification to creator
        send_notification(
            user_id=proposal.creator.id,
            notification_type='proposal_declined',
            title='Proposal Declined',
            body=f'Your proposal for {proposal.offer.title} was not accepted',
            deep_link=f'/offers/{proposal.offer.id}'
        )

        return Response({'message': 'Proposal declined successfully'})


from django.db import models
