"""
Cron job: Brand subscription renewal (monthly, 1st at 00:00)
Resets deals_used counter for active subscriptions and handles renewals.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.payments.models import Subscription
from apps.notifications.utils import send_notification


class Command(BaseCommand):
    help = 'Renew brand subscriptions monthly'

    def handle(self, *args, **kwargs):
        self.stdout.write('Processing subscription renewals...')

        # Get active subscriptions up for renewal
        subscriptions = Subscription.objects.filter(
            status='active',
            current_period_end__lt=timezone.now() + timedelta(days=3)
        )

        renewed = 0
        cancelled = 0

        for sub in subscriptions:
            # Reset deals used
            sub.reset_deals_used()

            # Extend period
            sub.current_period_end = timezone.now() + timedelta(days=30)
            sub.save()
            renewed += 1

            send_notification(
                user=sub.brand,
                title='Subscription Renewed',
                body=f'Your {sub.plan} plan has been renewed. {sub.deals_included} deals available.',
                data={'subscription_id': str(sub.id), 'type': 'subscription_renewed'}
            )

        # Mark past due subscriptions as cancelled
        past_due = Subscription.objects.filter(
            status='past_due',
            current_period_end__lt=timezone.now() - timedelta(days=7)
        )

        for sub in past_due:
            sub.status = 'cancelled'
            sub.save()
            cancelled += 1

        self.stdout.write(self.style.SUCCESS(f'Renewed {renewed}, cancelled {cancelled} subscriptions'))
