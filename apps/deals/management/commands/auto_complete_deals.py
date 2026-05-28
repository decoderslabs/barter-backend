"""
Cron job: Auto-complete delivered deals after 48h (daily at 8 AM)
Deals that have been in 'delivered' status for 48+ hours are auto-completed.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.deals.models import Deal
from apps.notifications.utils import send_notification


class Command(BaseCommand):
    help = 'Auto-complete delivered deals after 48 hours'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking for deals to auto-complete...')

        # Find delivered deals older than 48 hours
        to_complete = Deal.objects.filter(
            status='delivered',
            updated_at__lt=timezone.now() - timedelta(hours=48)
        )

        count = 0
        for deal in to_complete:
            # Mark as complete
            deal.status = 'complete'
            deal.completed_at = timezone.now()
            deal.save()

            # Trigger ratings
            send_notification(
                user=deal.creator,
                title='Deal Completed',
                body=f'"{deal.offer.title}" is complete. Rate your experience!',
                data={'deal_id': str(deal.id), 'type': 'deal_complete'}
            )
            send_notification(
                user=deal.brand,
                title='Deal Completed',
                body=f'"{deal.offer.title}" is complete. Rate {deal.creator.username}!',
                data={'deal_id': str(deal.id), 'type': 'deal_complete'}
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Auto-completed {count} deals'))
