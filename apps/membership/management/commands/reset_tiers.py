"""
Cron job: Reset membership tiers and recalculate creator tiers (monthly, 1st at 00:00)
Resets monthly points and recalculates all creator tiers based on current stats.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.membership.models import CreatorMembership
from apps.users.models import CreatorProfile, SocialAccount


class Command(BaseCommand):
    help = 'Reset membership tiers and recalculate creator tiers monthly'

    def handle(self, *args, **kwargs):
        self.stdout.write('Resetting membership tiers...')

        memberships = CreatorMembership.objects.all()
        count = 0

        for membership in memberships:
            # Reset monthly points
            membership.monthly_points = 0
            membership.points_to_next_pro = max(0, 500 - membership.total_points)

            # Check pro status expiry
            if membership.pro_until and membership.pro_until < timezone.now().date():
                membership.pro_status = False
                membership.pro_until = None

            membership.save()
            count += 1

        self.stdout.write(f'Reset {count} memberships')

        # Recalculate creator tiers
        self.stdout.write('Recalculating creator tiers...')
        profiles = CreatorProfile.objects.all()

        for profile in profiles:
            profile.calculate_tier()

        self.stdout.write(self.style.SUCCESS(f'Recalculated {profiles.count()} creator tiers'))
