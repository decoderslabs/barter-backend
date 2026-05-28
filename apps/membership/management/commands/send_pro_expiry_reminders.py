from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.membership.models import CreatorMembership
from apps.notifications.utils import send_notification


class Command(BaseCommand):
    help = 'Send reminders to creators whose Pro membership is expiring in 14 days'

    def handle(self, *args, **options):
        fourteen_days_from_now = timezone.now() + timedelta(days=14)
        
        expiring_memberships = CreatorMembership.objects.filter(
            pro_active=True,
            pro_expires_at__lte=fourteen_days_from_now,
            pro_expires_at__gt=timezone.now()
        )
        
        count = 0
        for membership in expiring_memberships:
            days_remaining = (membership.pro_expires_at - timezone.now()).days
            
            send_notification(
                user_id=str(membership.creator.id),
                notification_type='pro_expiry_reminder',
                title='Pro Membership Expiring Soon',
                body=f'Your Pro membership expires in {days_remaining} days. Complete more tasks to extend it!',
                deep_link='membership://status',
                send_email=True
            )
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent expiry reminders to {count} creators')
        )
