from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Q, Sum
from apps.offers.models import Offer
from apps.proposals.models import Proposal
from apps.deals.models import Deal


class IsBrand(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['brand', 'both']


class BrandDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def get(self, request):
        user = request.user

        # Get stats
        active_offers = Offer.objects.filter(brand=user, status='live').count()
        total_proposals = Proposal.objects.filter(offer__brand=user).count()
        pending_proposals = Proposal.objects.filter(offer__brand=user, status='pending').count()
        active_deals = Deal.objects.filter(brand=user, status='active').count()
        completed_deals = Deal.objects.filter(brand=user, status='completed').count()

        # Recent proposals
        recent_proposals = Proposal.objects.filter(
            offer__brand=user
        ).select_related('creator', 'offer').order_by('-created_at')[:5]

        proposal_data = []
        for prop in recent_proposals:
            proposal_data.append({
                'id': str(prop.id),
                'offer_title': prop.offer.title,
                'creator_username': prop.creator.username,
                'creator_name': prop.creator.name,
                'status': prop.status,
                'created_at': prop.created_at.isoformat()
            })

        # Recent deals
        recent_deals = Deal.objects.filter(
            brand=user
        ).select_related('creator', 'offer').order_by('-created_at')[:5]

        deal_data = []
        for deal in recent_deals:
            deal_data.append({
                'id': str(deal.id),
                'offer_title': deal.offer.title,
                'creator_username': deal.creator.username,
                'creator_name': deal.creator.name,
                'status': deal.status,
                'deal_fee': float(deal.deal_fee),
                'currency': deal.currency,
                'created_at': deal.created_at.isoformat()
            })

        data = {
            'stats': {
                'active_offers': active_offers,
                'total_proposals': total_proposals,
                'pending_proposals': pending_proposals,
                'active_deals': active_deals,
                'completed_deals': completed_deals
            },
            'recent_proposals': proposal_data,
            'recent_deals': deal_data
        }

        return Response(data)


class BrandInboxView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def get(self, request):
        user = request.user
        status_filter = request.query_params.get('status', None)

        proposals = Proposal.objects.filter(
            offer__brand=user
        ).select_related('creator', 'offer')

        if status_filter:
            proposals = proposals.filter(status=status_filter)

        proposals = proposals.order_by('-created_at')

        proposal_data = []
        for prop in proposals:
            proposal_data.append({
                'id': str(prop.id),
                'offer_id': str(prop.offer.id),
                'offer_title': prop.offer.title,
                'creator_id': str(prop.creator.id),
                'creator_username': prop.creator.username,
                'creator_name': prop.creator.name,
                'status': prop.status,
                'pitch': prop.pitch,
                'deliverables': prop.deliverables,
                'timeline': prop.timeline.isoformat() if prop.timeline else None,
                'round_number': prop.round_number,
                'can_counter': prop.can_counter(),
                'created_at': prop.created_at.isoformat(),
                'updated_at': prop.updated_at.isoformat()
            })

        return Response(proposal_data)
