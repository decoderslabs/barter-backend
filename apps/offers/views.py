from rest_framework import generics, status, filters, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Offer
from .serializers import (
    OfferSerializer, OfferCreateSerializer, OfferUpdateSerializer,
    OfferListSerializer, ValueEngineSerializer
)


class IsBrand(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['brand', 'both']


class OfferListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'currency', 'rights_tier', 'exclusivity']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'estimated_value', 'quantity_remaining']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OfferCreateSerializer
        return OfferListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsBrand()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = Offer.objects.filter(status='live')

        # Filter by niche (in kpi_preferences)
        niche = self.request.query_params.get('niche')
        if niche:
            queryset = queryset.filter(kpi_preferences__niches__contains=[niche])

        # Filter by market (location_country of brand)
        market = self.request.query_params.get('market')
        if market:
            queryset = queryset.filter(brand__location_country__iexact=market)

        # Filter by drops
        drops = self.request.query_params.get('drops')
        if drops:
            from apps.drops.models import DropsCampaign
            drops_offer_ids = DropsCampaign.objects.values_list('offer_id', flat=True)
            if drops.lower() == 'true':
                queryset = queryset.filter(id__in=drops_offer_ids)
            else:
                queryset = queryset.exclude(id__in=drops_offer_ids)

        # Filter by value range
        min_value = self.request.query_params.get('min_value')
        max_value = self.request.query_params.get('max_value')
        if min_value:
            queryset = queryset.filter(estimated_value__gte=min_value)
        if max_value:
            queryset = queryset.filter(estimated_value__lte=max_value)

        return queryset.select_related('brand')

    def perform_create(self, serializer):
        serializer.save(brand=self.request.user)


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return OfferUpdateSerializer
        return OfferSerializer

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.brand != request.user:
                self.permission_denied(request, message="Only the brand owner can modify this offer")


class ValueEngineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            offer = Offer.objects.get(id=id, status='live')
        except Offer.DoesNotExist:
            return Response({'error': 'Offer not found'}, status=404)

        value = offer.estimated_value
        currency = offer.currency

        # Simple recommendation logic based on offer value
        if value < 5000:
            post_count = 1
            platforms = ['instagram']
            content_types = ['story', 'reel']
        elif value < 15000:
            post_count = 2
            platforms = ['instagram', 'tiktok']
            content_types = ['reel', 'post']
        elif value < 50000:
            post_count = 3
            platforms = ['instagram', 'tiktok', 'youtube']
            content_types = ['reel', 'video', 'post']
        else:
            post_count = 5
            platforms = ['instagram', 'tiktok', 'youtube', 'linkedin']
            content_types = ['video', 'post', 'story']

        estimated_engagement = int(value / 100)

        similar_offers = Offer.objects.filter(
            type=offer.type,
            estimated_value__gte=value * 0.8,
            estimated_value__lte=value * 1.2,
            status='live'
        ).exclude(id=offer.id).count()

        data = {
            'offer_id': offer.id,
            'estimated_value': value,
            'currency': currency,
            'recommended_content_types': content_types,
            'recommended_platforms': platforms,
            'recommended_post_count': post_count,
            'estimated_engagement': estimated_engagement,
            'similar_offers_count': similar_offers
        }

        serializer = ValueEngineSerializer(data)
        return Response(serializer.data)


class MyOffersView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated, IsBrand]

    def get_queryset(self):
        return Offer.objects.filter(brand=self.request.user).order_by('-created_at')
