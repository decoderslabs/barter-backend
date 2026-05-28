import uuid
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from .models import Payment, Subscription, Wallet
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer,
    SubscriptionSerializer, SubscriptionCreateSerializer
)


class IsBrand(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['brand', 'both']


class CreateDealFeePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        from apps.deals.models import Deal
        try:
            deal = Deal.objects.get(id=serializer.validated_data['deal_id'])
        except Deal.DoesNotExist:
            return Response({'error': 'Deal not found'}, status=404)

        if deal.brand != request.user:
            return Response({'error': 'Access denied'}, status=403)

        gateway = serializer.validated_data['gateway']

        # Stub: Create mock payment record
        # In production, this would integrate with Razorpay/Stripe SDK
        mock_order_id = f"order_{uuid.uuid4().hex[:16]}"

        payment = Payment.objects.create(
            brand=request.user,
            deal=deal,
            amount=deal.deal_fee,
            currency=deal.currency,
            gateway=gateway,
            gateway_ref=mock_order_id,
            status='pending'
        )

        return Response({
            'payment_id': str(payment.id),
            'order_id': mock_order_id,
            'amount': str(deal.deal_fee),
            'currency': deal.currency,
            'gateway': gateway,
            'key': settings.RAZORPAY_KEY_ID if gateway == 'razorpay' else settings.STRIPE_SECRET_KEY[:20] if settings.STRIPE_SECRET_KEY else 'mock_key'
        })


class RazorpayWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import hmac
        import hashlib
        import razorpay
        from django.conf import settings
        
        # Verify signature
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        received_signature = request.headers.get('X-Razorpay-Signature')
        payload = request.body.decode('utf-8')
        
        if not received_signature:
            return Response({'error': 'Missing signature'}, status=400)
        
        # Generate expected signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(received_signature, expected_signature):
            return Response({'error': 'Invalid signature'}, status=400)
        
        # Process webhook event
        event = request.data.get('event')
        payload_data = request.data.get('payload', {})
        
        if event == 'payment.captured':
            payment_entity = payload_data.get('payment', {}).get('entity', {})
            order_id = payment_entity.get('order_id')
            razorpay_payment_id = payment_entity.get('id')
            
            # Find payment by gateway_ref
            try:
                payment = Payment.objects.get(gateway_ref=order_id)
                payment.status = 'completed'
                payment.gateway_ref = razorpay_payment_id
                payment.save()
                
                # Generate invoice (stub)
                payment.invoice_url = f"https://barter-storage.example.com/invoices/{payment.id}.pdf"
                payment.save()
                
            except Payment.DoesNotExist:
                pass
        
        return Response({'status': 'received'})


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import stripe
        from django.conf import settings
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Verify signature
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            return Response({'error': 'Missing signature'}, status=400)
        
        try:
            event = stripe.Webhook.construct_event(
                request.body.decode('utf-8'),
                signature,
                webhook_secret
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return Response({'error': 'Invalid signature'}, status=400)
        
        # Process event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']
            
            try:
                payment = Payment.objects.get(gateway_ref=payment_intent_id)
                payment.status = 'completed'
                payment.save()
                
                # Generate invoice
                payment.invoice_url = f"https://barter-storage.example.com/invoices/{payment.id}.pdf"
                payment.save()
                
            except Payment.DoesNotExist:
                pass
        
        elif event['type'] == 'invoice.paid':
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')
            
            try:
                subscription = Subscription.objects.get(gateway_sub_id=subscription_id)
                subscription.status = 'active'
                subscription.current_period_end = invoice.get('period_end')
                subscription.save()
            except Subscription.DoesNotExist:
                pass
        
        return Response({'status': 'received'})


class InvoiceListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            brand=self.request.user,
            status='completed'
        ).order_by('-created_at')


class SubscriptionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def post(self, request):
        serializer = SubscriptionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        plan = serializer.validated_data['plan']
        gateway = serializer.validated_data['gateway']

        # Stub: Create mock subscription
        # In production, integrate with Razorpay/Stripe SDK
        mock_sub_id = f"sub_{uuid.uuid4().hex[:16]}"

        deals_included = {'starter': 5, 'growth': 15, 'scale': 50}.get(plan, 5)

        from django.utils import timezone
        from datetime import timedelta

        subscription = Subscription.objects.create(
            brand=request.user,
            plan=plan,
            gateway=gateway,
            gateway_sub_id=mock_sub_id,
            status='active',
            current_period_end=timezone.now() + timedelta(days=30),
            deals_included=deals_included
        )

        return Response(SubscriptionSerializer(subscription).data)


class MySubscriptionView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def get_object(self):
        return Subscription.objects.filter(
            brand=self.request.user,
            status='active'
        ).first()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({'plan': 'free', 'status': 'active'})
        return Response(self.get_serializer(instance).data)


class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsBrand]

    def delete(self, request):
        subscription = Subscription.objects.filter(
            brand=request.user,
            status='active'
        ).first()

        if not subscription:
            return Response({'error': 'No active subscription'}, status=404)

        # Stub: In production, cancel via gateway API
        subscription.status = 'cancelled'
        subscription.save()

        return Response({'message': 'Subscription cancelled'})


class MyWalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        return Response({
            'balance': wallet.balance,
            'lifetime_earned': wallet.lifetime_earned,
            'lifetime_spent': wallet.lifetime_spent,
            'updated_at': wallet.updated_at
        })


class WalletTransactionsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        transactions = [
            {
                'id': str(t.id),
                'type': t.type,
                'amount': t.amount,
                'description': t.description,
                'source': t.source,
                'created_at': t.created_at
            }
            for t in queryset
        ]
        return Response(transactions)


class TransferPointsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_username = request.data.get('to_username')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if not to_username or not amount:
            return Response({'error': 'to_username and amount required'}, status=400)

        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return Response({'error': 'amount must be a positive integer'}, status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            to_user = User.objects.get(username=to_username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        if to_user == request.user:
            return Response({'error': 'Cannot transfer to yourself'}, status=400)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        try:
            wallet.transfer_points(to_user, amount, description)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        return Response({
            'message': f'Successfully transferred {amount} points to {to_username}',
            'new_balance': wallet.balance
        })
