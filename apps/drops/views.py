from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import csv
from django.http import HttpResponse

from .models import DropsCampaign, DropsApplication
from .serializers import (
    DropsCampaignSerializer, DropsCampaignCreateSerializer,
    DropsApplicationSerializer, DropsApplicationCreateSerializer
)
from apps.notifications.utils import send_notification


class IsBrand(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['brand', 'both']


class IsCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['creator', 'both']


class DropsListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DropsCampaignCreateSerializer
        return DropsCampaignSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsBrand()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return DropsCampaign.objects.filter(status='live').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(brand=self.request.user)


class DropsDetailView(generics.RetrieveUpdateAPIView):
    queryset = DropsCampaign.objects.all()
    serializer_class = DropsCampaignSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsBrand()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ['PUT', 'PATCH']:
            if obj.brand != request.user:
                self.permission_denied(request, message="Only the brand owner can modify")


class ApplyToDropsView(generics.CreateAPIView):
    serializer_class = DropsApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def perform_create(self, serializer):
        application = serializer.save()

        send_notification(
            user_id=application.campaign.brand.id,
            notification_type='drops_application',
            title='New Drops Application',
            body=f'{application.creator.name} applied to {application.campaign.name}',
            deep_link=f'/drops/{application.campaign.id}/applications'
        )

        return application


class DropsApplicationsListView(generics.ListAPIView):
    serializer_class = DropsApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def get_queryset(self):
        campaign_id = self.kwargs.get('id')
        return DropsApplication.objects.filter(campaign_id=campaign_id).order_by('-applied_at')

    def check_permissions(self, request):
        super().check_permissions(request)
        try:
            campaign = DropsCampaign.objects.get(id=self.kwargs.get('id'))
            if campaign.brand != request.user:
                self.permission_denied(request, message="Only campaign owner can view applications")
        except DropsCampaign.DoesNotExist:
            pass


class ApproveApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id, app_id):
        try:
            campaign = DropsCampaign.objects.get(id=id)
            application = DropsApplication.objects.get(id=app_id, campaign=campaign)
        except (DropsCampaign.DoesNotExist, DropsApplication.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        if campaign.brand != request.user:
            return Response({'error': 'Access denied'}, status=403)

        if application.status != 'pending':
            return Response({'error': 'Application already processed'}, status=400)

        # Create deal from drops
        from apps.deals.models import Deal
        deal = Deal.objects.create(
            offer=campaign.offer,
            brand=campaign.brand,
            creator=application.creator,
            agreed_terms={
                'campaign_name': campaign.name,
                'offer_title': campaign.offer.title,
                'creator_pitch': application.pitch,
            },
            rights_tier=campaign.offer.rights_tier,
            raw_files_required=campaign.offer.raw_files_required,
            exclusivity=campaign.offer.exclusivity,
            deal_fee=0,  # Drops deals may have different fee structure
            currency=campaign.offer.currency,
            status='active',
            deadline=campaign.application_deadline,
        )

        application.status = 'approved'
        application.deal = deal
        application.reviewed_at = timezone.now()
        application.save()

        campaign.fill_slot()

        send_notification(
            user_id=application.creator.id,
            notification_type='drops_approved',
            title='Application Approved!',
            body=f'You have been approved for {campaign.name}',
            deep_link=f'/deals/{deal.id}'
        )

        return Response({'message': 'Application approved', 'deal_id': str(deal.id)})


class DeclineApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request, id, app_id):
        try:
            campaign = DropsCampaign.objects.get(id=id)
            application = DropsApplication.objects.get(id=app_id, campaign=campaign)
        except (DropsCampaign.DoesNotExist, DropsApplication.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        if campaign.brand != request.user:
            return Response({'error': 'Access denied'}, status=403)

        if application.status != 'pending':
            return Response({'error': 'Application already processed'}, status=400)

        application.status = 'declined'
        application.reviewed_at = timezone.now()
        application.save()

        send_notification(
            user_id=application.creator.id,
            notification_type='drops_declined',
            title='Application Declined',
            body=f'Your application for {campaign.name} was not accepted',
            deep_link=f'/drops/{campaign.id}'
        )

        return Response({'message': 'Application declined'})


class ShippingExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def get(self, request, id):
        try:
            campaign = DropsCampaign.objects.get(id=id)
        except DropsCampaign.DoesNotExist:
            return Response({'error': 'Campaign not found'}, status=404)

        if campaign.brand != request.user:
            return Response({'error': 'Access denied'}, status=403)

        approved_apps = DropsApplication.objects.filter(
            campaign=campaign,
            status='approved',
            deal__isnull=False
        ).select_related('creator', 'deal')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{campaign.name}_shipping.csv"'

        writer = csv.writer(response)
        writer.writerow(['Creator Name', 'Username', 'Email', 'Shipping Address', 'Deal ID'])

        for app in approved_apps:
            shipping = app.deal.get_shipping_address() if app.deal else None
            writer.writerow([
                app.creator.name,
                app.creator.username,
                app.creator.email,
                shipping.get('address', '') if shipping else '',
                str(app.deal.id) if app.deal else ''
            ])

        return response


from django.utils import timezone
