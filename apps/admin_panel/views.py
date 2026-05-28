from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from django.db.models import Count, Q, Avg, Sum, Case, When, F, DurationField
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.offers.models import Offer
from apps.proposals.models import Proposal
from apps.deals.models import Deal
from apps.users.models import User, SocialAccount
from apps.ratings.models import Rating


class DealsAnalyticsView(APIView):
    """Analytics for brand's deals"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['brand', 'both']:
            return Response({'error': 'Only brands can view analytics'}, status=403)

        brand = request.user
        deals = Deal.objects.filter(brand=brand)

        # Basic stats
        total_deals = deals.count()
        active_deals = deals.filter(status='active').count()
        completed_deals = deals.filter(status='complete').count()
        disputed_deals = deals.filter(status='disputed').count()

        # Completion rate
        completion_rate = (completed_deals / total_deals * 100) if total_deals > 0 else 0

        # Average deal value
        avg_deal_value = deals.aggregate(
            avg_value=Avg('agreed_terms__offer_estimated_value')
        )['avg_value'] or 0

        # Deals by status
        deals_by_status = deals.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        # Recent deals (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_deals = deals.filter(created_at__gte=thirty_days_ago).count()

        # Deals over time (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        deals_over_time = deals.filter(
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        return Response({
            'total_deals': total_deals,
            'active_deals': active_deals,
            'completed_deals': completed_deals,
            'disputed_deals': disputed_deals,
            'completion_rate': round(completion_rate, 2),
            'avg_deal_value': avg_deal_value,
            'deals_by_status': list(deals_by_status),
            'recent_deals_30_days': recent_deals,
            'deals_over_time': list(deals_over_time),
        })


class CreatorsAnalyticsView(APIView):
    """Analytics for creators brand has worked with"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['brand', 'both']:
            return Response({'error': 'Only brands can view analytics'}, status=403)

        brand = request.user
        deals = Deal.objects.filter(brand=brand)

        # Top creators by deal count
        top_creators = deals.values(
            'creator__id', 'creator__username', 'creator__barter_score'
        ).annotate(
            deal_count=Count('id')
        ).order_by('-deal_count')[:10]

        # Creator tiers distribution
        creator_tiers = deals.values(
            'creator__creator_profile__tier'
        ).annotate(
            count=Count('id')
        ).order_by('creator__creator_profile__tier')

        # Average creator barter score
        avg_barter_score = deals.aggregate(
            avg_score=Avg('creator__barter_score')
        )['avg_score'] or 0

        return Response({
            'top_creators': list(top_creators),
            'creator_tiers': list(creator_tiers),
            'avg_creator_barter_score': round(avg_barter_score, 2),
        })


class ContentAnalyticsView(APIView):
    """Analytics for content deliverables"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['brand', 'both']:
            return Response({'error': 'Only brands can view analytics'}, status=403)

        brand = request.user
        deals = Deal.objects.filter(brand=brand, status='complete')

        # Content types delivered
        content_types = {}
        for deal in deals:
            agreed_terms = deal.agreed_terms or {}
            deliverables = agreed_terms.get('deliverables', [])
            for deliverable in deliverables:
                content_type = deliverable.get('content_type', 'unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1

        # Platform distribution
        platforms = {}
        for deal in deals:
            agreed_terms = deal.agreed_terms or {}
            deliverables = agreed_terms.get('deliverables', [])
            for deliverable in deliverables:
                platform = deliverable.get('platform', 'unknown')
                platforms[platform] = platforms.get(platform, 0) + 1

        # Average delivery time (from deal creation to completion)
        avg_delivery_days = deals.aggregate(
            avg_days=Avg(
                Case(
                    When(completed_at__isnull=False, then=F('completed_at') - F('created_at')),
                    output_field=DurationField()
                )
            )
        )['avg_days']

        return Response({
            'content_types': content_types,
            'platforms': platforms,
            'avg_delivery_days': avg_delivery_days.days if avg_delivery_days else 0,
        })
