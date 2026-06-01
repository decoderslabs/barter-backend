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
            avg_value=Avg('deal_fee')
        )['avg_value'] or 0

        # Estimated total barter value
        total_barter_value = deals.aggregate(
            total=Sum('deal_fee')
        )['total'] or 0

        # KPIs
        kpis = [
            {
                'id': 'deals',
                'label': 'Total Deals',
                'value': total_deals,
                'trend_label': '+12%',
                'trend_up': True
            },
            {
                'id': 'completed',
                'label': 'Completed',
                'value': completed_deals,
                'trend_label': f'{active_deals} Active',
                'trend_up': None
            },
            {
                'id': 'value',
                'label': 'Est. Barter Value',
                'value': int(total_barter_value),
                'value_suffix': None,
                'trend_label': None,
                'trend_up': None,
                'progress': None
            }
        ]

        # Reach chart (mock data - in production, this would come from social media analytics)
        six_months_ago = timezone.now() - timedelta(days=180)
        reach_chart = []
        for i in range(6):
            month = six_months_ago + timedelta(days=30 * i)
            import random
            reach_chart.append({
                'month': month.strftime('%Y-%m'),
                'reach': random.randint(2000000, 5000000)
            })

        # Engagement chart (mock data)
        engagement_chart = []
        for i in range(6):
            month = six_months_ago + timedelta(days=30 * i)
            engagement_chart.append({
                'month': month.strftime('%Y-%m'),
                'rate': round(random.uniform(3.0, 7.0), 1)
            })

        # Platform breakdown (mock data based on offer content_ask)
        platform_breakdown = [
            {'platform': 'instagram', 'share': 0.54, 'reach': 1728000, 'deals': int(total_deals * 0.54) if total_deals > 0 else 0},
            {'platform': 'tiktok', 'share': 0.30, 'reach': 960000, 'deals': int(total_deals * 0.30) if total_deals > 0 else 0},
            {'platform': 'youtube', 'share': 0.16, 'reach': 512000, 'deals': int(total_deals * 0.16) if total_deals > 0 else 0},
        ]

        # Content performance (mock data from completed deals)
        content_performance = []
        completed_deals_list = deals.filter(status='complete').select_related('creator', 'offer')[:10]
        for idx, deal in enumerate(completed_deals_list):
            import random
            content_performance.append({
                'id': f'cp_{idx:03d}',
                'creator_name': deal.creator.name,
                'creator_avatar': deal.creator.profile_photo_url or '',
                'campaign_title': deal.offer.title,
                'platform': 'instagram',
                'content_type': 'reel',
                'reach': random.randint(100000, 500000),
                'engagement_rate': round(random.uniform(3.0, 8.0), 1),
                'clicks': random.randint(1000, 5000),
                'conversions': random.randint(50, 300),
                'barter_value': str(deal.deal_fee),
                'currency': deal.currency,
                'posted_date': deal.completed_at.strftime('%Y-%m-%d') if deal.completed_at else ''
            })

        # Top creators
        top_creators_data = deals.values(
            'creator__name', 'creator__barter_score'
        ).annotate(
            deal_count=Count('id')
        ).order_by('-deal_count')[:5]

        top_creators = []
        for idx, creator in enumerate(top_creators_data, 1):
            import random
            top_creators.append({
                'rank': idx,
                'name': creator['creator__name'],
                'deals': creator['deal_count'],
                'total_reach': random.randint(500000, 2000000),
                'avg_rating': round(creator['creator__barter_score'] or 4.5, 1)
            })

        return Response({
            'kpis': kpis,
            'reach_chart_title': 'Monthly Reach',
            'reach_chart': reach_chart,
            'engagement_chart': engagement_chart,
            'platform_breakdown': platform_breakdown,
            'content_performance_title': 'Content Performance',
            'content_performance': content_performance,
            'top_creators': top_creators
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
