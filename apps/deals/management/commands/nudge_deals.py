"""
Cron job: Nudge due deals (daily at 8 AM)
Send reminders to creators with active deals approaching deadline.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.deals.models import Deal
from apps.notifications.utils import send_notification


class Command(BaseCommand):
    help = 'Nudge creators with due deals'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking for deals needing nudges...')

        # Deals due within 3 days
        upcoming = Deal.objects.filter(
            status='active',
            deadline__lte=timezone.now().date() + timedelta(days=3),
            deadline__gt=timezone.now().date()
        )

        # Overdue deals
        overdue = Deal.objects.filter(
            status='active',
            deadline__lt=timezone.now().date()
        )

        count = 0

        for deal in upcoming:
            days_left = (deal.deadline - timezone.now().date()).days
            send_notification(
                user=deal.creator,
                title='Deal Reminder',
                body=f'Deadline in {days_left} days for "{deal.offer.title}".',
                data={'deal_id': str(deal.id), 'type': 'deal_nudge'}
            )
            count += 1

        for deal in overdue:
            days_overdue = (timezone.now().date() - deal.deadline).days
            send_notification(
                user=deal.creator,
                title='Deal Overdue',
                body=f'Deadline was {days_overdue} days ago for "{deal.offer.title}".',
                data={'deal_id': str(deal.id), 'type': 'deal_overdue'}
            )
            send_notification(
                user=deal.brand,
                title='Deal Overdue',
                body=f'{deal.creator.username} is {days_overdue} days overdue.',
                data={'deal_id': str(deal.id), 'type': 'deal_overdue'}
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Sent {count} deal nudges'))
