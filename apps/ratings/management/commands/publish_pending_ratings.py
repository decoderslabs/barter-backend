from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.ratings.models import Rating
from apps.notifications.utils import send_notification
from apps.users.models import User


class Command(BaseCommand):
    help = 'Publish ratings that are 7 days old (both parties have rated)'

    def handle(self, *args, **options):
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Find ratings where both parties have rated but not published yet
        # This requires checking if both parties in a deal have rated
        from apps.deals.models import Deal
        
        deals_with_both_ratings = Deal.objects.filter(
            status='complete',
            completed_at__lte=seven_days_ago
        ).annotate(
            rating_count=Count('rating')
        ).filter(rating_count__gte=2)
        
        count = 0
        for deal in deals_with_both_ratings:
            ratings = Rating.objects.filter(deal=deal, published_at__isnull=True)
            
            for rating in ratings:
                rating.published_at = timezone.now()
                rating.save()
                count += 1
            
            # Recalculate barter scores for both parties
            deal.brand.recalculate_barter_score()
            deal.creator.recalculate_barter_score()
        
        self.stdout.write(
            self.style.SUCCESS(f'Published {count} ratings and updated barter scores')
        )
