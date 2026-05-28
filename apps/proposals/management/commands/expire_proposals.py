"""
Cron job: Mark expired proposals (daily at 8 AM)
Proposals that have passed their round deadline are marked as expired.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.proposals.models import Proposal
from apps.notifications.utils import send_notification


class Command(BaseCommand):
    help = 'Mark expired proposals'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking for expired proposals...')

        # Find pending/countered proposals past deadline
        expired = Proposal.objects.filter(
            status__in=['pending', 'countered'],
            updated_at__lt=timezone.now() - timezone.timedelta(days=30)  # 30 day expiry
        )

        count = 0
        for proposal in expired:
            proposal.status = 'expired'
            proposal.save()
            count += 1

            # Notify both parties
            send_notification(
                user=proposal.creator,
                title='Proposal Expired',
                body=f'Your proposal for "{proposal.offer.title}" has expired.',
                data={'proposal_id': str(proposal.id), 'type': 'proposal_expired'}
            )
            send_notification(
                user=proposal.offer.brand,
                title='Proposal Expired',
                body=f'Proposal from {proposal.creator.username} has expired.',
                data={'proposal_id': str(proposal.id), 'type': 'proposal_expired'}
            )

        self.stdout.write(self.style.SUCCESS(f'Marked {count} proposals as expired'))
