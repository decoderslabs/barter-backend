import uuid
from django.db import models
from django.conf import settings


class Rating(models.Model):
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given')
    ratee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_received')
    stars = models.PositiveSmallIntegerField(default=0)  # 1-5, 0 = pending
    review_text = models.CharField(max_length=280, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ratings'
        ordering = ['-created_at']
        unique_together = ['deal', 'rater']

    def __str__(self):
        return f"{self.rater.username} rated {self.ratee.username}: {self.stars}"

    def publish(self):
        # Check if both parties have rated
        other_rating = Rating.objects.filter(
            deal=self.deal
        ).exclude(rater=self.rater).first()

        self.published_at = timezone.now()
        self.save()

        if other_rating and other_rating.published_at:
            other_rating.published_at = timezone.now()
            other_rating.save()

            # Recalculate barter scores for both users
            self.ratee.update_barter_score()
            self.rater.update_barter_score()
