from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from apps.payments.models import Subscription


class Command(BaseCommand):
    help = 'Reset monthly deal count for subscriptions (runs on 1st of each month)'

    def handle(self, *args, **options):
        today = date.today()
        
        # Only run on the first day of the month
        if today.day != 1:
            self.stdout.write(self.style.WARNING('Not the first of the month, skipping'))
            return
        
        subscriptions = Subscription.objects.filter(status='active')
        
        count = 0
        for subscription in subscriptions:
            subscription.deals_used = 0
            subscription.save()
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Reset deal count for {count} active subscriptions')
        )
