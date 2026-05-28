from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from apps.membership.models import CreatorMembership


class Command(BaseCommand):
    help = 'Reset membership periods for creators based on their tier'

    def handle(self, *args, **options):
        now = timezone.now()
        today = date.today()
        
        memberships = CreatorMembership.objects.all()
        reset_count = 0
        
        for membership in memberships:
            if membership.period_reset_at <= now:
                # Clear tasks_this_period
                membership.tasks_this_period = {}
                
                # Calculate next reset date based on tier
                tier = membership.tier
                if tier in ['nano', 'micro']:
                    # Reset on first day of next month
                    if today.month == 12:
                        next_reset = date(today.year + 1, 1, 1)
                    else:
                        next_reset = date(today.year, today.month + 1, 1)
                else:  # mid, macro, mega
                    # Reset on first day of next quarter
                    quarter = (today.month - 1) // 3 + 1
                    if quarter == 4:
                        next_reset = date(today.year + 1, 1, 1)
                    else:
                        next_reset = date(today.year, (quarter * 3) + 1, 1)
                
                membership.period_reset_at = timezone.datetime.combine(
                    next_reset, timezone.datetime.min.time()
                ).replace(tzinfo=timezone.utc)
                membership.save()
                reset_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully reset {reset_count} membership periods')
        )
