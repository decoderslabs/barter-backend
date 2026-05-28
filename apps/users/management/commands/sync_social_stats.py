"""
Cron job: Sync social account stats every 12 hours
Updates follower counts, engagement rates, and average views.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import SocialAccount
from apps.users.oauth_utils import InstagramOAuth, TikTokOAuth, YouTubeOAuth


class Command(BaseCommand):
    help = 'Sync social account stats for all connected accounts'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting social stats sync...')

        accounts = SocialAccount.objects.all()
        updated = 0
        failed = 0

        for account in accounts:
            try:
                access_token = account.get_access_token()
                if not access_token:
                    continue

                if account.platform == 'instagram':
                    profile = InstagramOAuth.get_user_profile(access_token)
                    if profile:
                        account.handle = profile.get('username', account.handle)
                        account.followers = InstagramOAuth.get_followers(access_token)
                        account.engagement_rate = InstagramOAuth.calculate_engagement_rate(access_token, account.followers)

                elif account.platform == 'tiktok':
                    # Would need open_id stored - simplified for demo
                    pass

                elif account.platform == 'youtube':
                    channel = YouTubeOAuth.get_channel_info(access_token)
                    if channel:
                        stats = channel.get('statistics', {})
                        account.followers = stats.get('subscriberCount', account.followers)
                        channel_id = channel.get('id')
                        if channel_id:
                            account.avg_views = YouTubeOAuth.calculate_avg_views(access_token, channel_id)

                account.last_synced = timezone.now()
                account.save()
                updated += 1
                self.stdout.write(f'  Updated {account.platform} for {account.user.username}')

            except Exception as e:
                failed += 1
                self.stdout.write(f'  Failed {account.platform} for {account.user.username}: {e}')

        self.stdout.write(self.style.SUCCESS(f'Sync complete: {updated} updated, {failed} failed'))
