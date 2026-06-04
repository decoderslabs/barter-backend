from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.template.loader import render_to_string
import tempfile
import os
from django.conf import settings
from supabase import create_client, Client

from apps.deals.models import Deal


class ContractPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            deal = Deal.objects.get(id=id)
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if request.user not in [deal.brand, deal.creator]:
            return Response({'error': 'Access denied'}, status=403)

        # Return existing contract URL if generated
        if deal.contract_url:
            return Response({
                'contract_url': deal.contract_url,
                'expires_in': 3600  # 1 hour
            })

        # Generate PDF
        contract_url = generate_contract_pdf(deal)
        if contract_url:
            deal.contract_url = contract_url
            deal.save()
            return Response({
                'contract_url': contract_url,
                'expires_in': 3600
            })

        return Response({'error': 'Failed to generate contract'}, status=500)


def generate_contract_pdf(deal):
    """Generate contract PDF using WeasyPrint and upload to Supabase"""
    try:
        # Lazy import WeasyPrint to avoid system dependency issues during migrations
        from weasyprint import HTML

        html_string = render_to_string('contracts/contract.html', {
            'deal': deal,
            'brand_profile': deal.brand.brand_profile,
            'creator_profile': deal.creator.creator_profile,
            'offer': deal.offer,
            'agreed_terms': deal.agreed_terms,
        })

        # Generate PDF
        pdf = HTML(string=html_string).write_pdf()

        # Upload to Supabase
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        file_path = f"contracts/{deal.id}/contract.pdf"

        supabase.storage.from_('barter-private').upload(
            file_path,
            pdf,
            {'content-type': 'application/pdf'}
        )

        # Get signed URL (expires in 1 hour)
        signed_url = supabase.storage.from_('barter-private').create_signed_url(
            file_path,
            3600
        )['signedUrl']

        return signed_url

    except Exception as e:
        print(f"Error generating contract PDF: {e}")
        return None
