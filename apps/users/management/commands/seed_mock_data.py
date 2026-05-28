"""
Management command to seed the database with realistic mock data for Barter.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seed database with mock data for development/demo'

    def handle(self, *args, **options):
        self.stdout.write('Seeding mock data...')
        self._create_users()
        self._create_offers()
        self._create_proposals()
        self._create_deals()
        self._create_drops()
        self._create_ratings()
        self.stdout.write(self.style.SUCCESS('Mock data seeded successfully!'))

    def _create_users(self):
        from apps.users.models import User, BrandProfile, CreatorProfile, SocialAccount

        brands_data = [
            {'email': 'zara@brand.com', 'username': 'zara_india', 'name': 'Zara India', 'location_country': 'IN'},
            {'email': 'nykaa@brand.com', 'username': 'nykaa_official', 'name': 'Nykaa', 'location_country': 'IN'},
            {'email': 'mamaearth@brand.com', 'username': 'mamaearth', 'name': 'Mamaearth', 'location_country': 'IN'},
            {'email': 'boat@brand.com', 'username': 'boat_lifestyle', 'name': 'boAt Lifestyle', 'location_country': 'IN'},
            {'email': 'mcaffeine@brand.com', 'username': 'mcaffeine', 'name': 'mCaffeine', 'location_country': 'IN'},
        ]

        self.brands = []
        for data in brands_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'name': data['name'],
                    'role': 'brand',
                    'location_country': data['location_country'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                BrandProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company_name': data['name'],
                        'industry': random.choice(['fashion', 'beauty', 'tech', 'lifestyle']),
                        'website': f"https://www.{data['username']}.com",
                        'domain_verified': True,
                    }
                )
            self.brands.append(user)

        self.stdout.write(f'  Created {len(self.brands)} brands')

        creators_data = [
            {'email': 'priya@creator.com', 'username': 'priya_lifestyle', 'name': 'Priya Sharma', 'location_country': 'IN', 'tier_idx': 1},
            {'email': 'rahul@creator.com', 'username': 'rahul_tech', 'name': 'Rahul Mehta', 'location_country': 'IN', 'tier_idx': 2},
            {'email': 'sneha@creator.com', 'username': 'sneha_beauty', 'name': 'Sneha Kapoor', 'location_country': 'IN', 'tier_idx': 1},
            {'email': 'arjun@creator.com', 'username': 'arjun_fitness', 'name': 'Arjun Nair', 'location_country': 'IN', 'tier_idx': 2},
            {'email': 'divya@creator.com', 'username': 'divya_food', 'name': 'Divya Reddy', 'location_country': 'IN', 'tier_idx': 0},
            {'email': 'karan@creator.com', 'username': 'karan_travel', 'name': 'Karan Bhatia', 'location_country': 'IN', 'tier_idx': 3},
            {'email': 'meera@creator.com', 'username': 'meera_fashion', 'name': 'Meera Joshi', 'location_country': 'IN', 'tier_idx': 1},
            {'email': 'vikram@creator.com', 'username': 'vikram_gaming', 'name': 'Vikram Singh', 'location_country': 'IN', 'tier_idx': 2},
        ]

        follower_ranges = [
            (5000, 9000, 'nano'),
            (12000, 45000, 'micro'),
            (80000, 150000, 'mid'),
            (300000, 800000, 'macro'),
            (1200000, 3000000, 'mega'),
        ]

        self.creators = []
        for data in creators_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'name': data['name'],
                    'role': 'creator',
                    'location_country': data['location_country'],
                    'is_active': True,
                    'barter_score': round(random.uniform(3.5, 5.0), 1),
                }
            )
            if created:
                user.set_password('password123')
                user.save()

                f_min, f_max, tier = follower_ranges[data['tier_idx']]
                followers = random.randint(f_min, f_max)

                CreatorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'tier': tier,
                        'niches': [random.choice(['beauty', 'skincare', 'tech', 'gadgets', 'food', 'fitness', 'travel', 'fashion'])],
                        'content_types': [random.choice(['reel', 'post', 'story', 'video'])],
                    }
                )
                SocialAccount.objects.get_or_create(
                    user=user,
                    platform='instagram',
                    defaults={
                        'handle': data['username'],
                        'followers': followers,
                        'engagement_rate': round(random.uniform(2.0, 8.5), 2),
                        'avg_views': random.randint(5000, 500000),
                    }
                )
            self.creators.append(user)

        self.stdout.write(f'  Created {len(self.creators)} creators')

    def _create_offers(self):
        from apps.offers.models import Offer

        offers_data = [
            {
                'brand': self.brands[0],
                'title': 'Summer Collection Launch - Styling Reels',
                'description': 'Looking for fashion-forward creators to showcase our new Summer 2025 collection.',
                'type': 'physical',
                'status': 'live',
                'estimated_value': 8500,
                'currency': 'INR',
                'quantity': 20,
                'quantity_remaining': 15,
                'rights_tier': 'standard',
                'exclusivity': 'none',
                'content_ask': {'types': ['reel', 'story'], 'count': 2, 'platforms': ['instagram']},
                'kpi_preferences': {'niches': ['fashion', 'lifestyle'], 'min_followers': 5000, 'min_engagement': 2.5},
            },
            {
                'brand': self.brands[1],
                'title': 'Skincare Routine Feature - Nykaa Naturals',
                'description': 'We want authentic skincare creators to feature our new Nykaa Naturals range.',
                'type': 'physical',
                'status': 'live',
                'estimated_value': 5000,
                'currency': 'INR',
                'quantity': 30,
                'quantity_remaining': 22,
                'rights_tier': 'standard',
                'exclusivity': 'category_30',
                'content_ask': {'types': ['reel', 'story'], 'count': 3, 'platforms': ['instagram']},
                'kpi_preferences': {'niches': ['beauty', 'skincare'], 'min_followers': 3000, 'min_engagement': 3.0},
            },
            {
                'brand': self.brands[2],
                'title': 'Honest Review - Mamaearth Vitamin C Range',
                'description': 'Looking for skincare enthusiasts to do honest reviews of our Vitamin C range.',
                'type': 'physical',
                'status': 'live',
                'estimated_value': 3500,
                'currency': 'INR',
                'quantity': 50,
                'quantity_remaining': 38,
                'rights_tier': 'extended',
                'exclusivity': 'none',
                'content_ask': {'types': ['reel', 'post'], 'count': 2, 'platforms': ['instagram', 'youtube']},
                'kpi_preferences': {'niches': ['beauty', 'skincare', 'lifestyle'], 'min_followers': 2000, 'min_engagement': 2.0},
            },
            {
                'brand': self.brands[3],
                'title': 'Unboxing + Review - boAt Airdopes 141',
                'description': 'Tech creators wanted for unboxing and review of our new boAt Airdopes 141 earbuds.',
                'type': 'physical',
                'status': 'live',
                'estimated_value': 12000,
                'currency': 'INR',
                'quantity': 15,
                'quantity_remaining': 10,
                'rights_tier': 'extended',
                'exclusivity': 'category_30',
                'content_ask': {'types': ['video', 'reel'], 'count': 2, 'platforms': ['youtube', 'instagram']},
                'kpi_preferences': {'niches': ['tech', 'gadgets', 'lifestyle'], 'min_followers': 10000, 'min_engagement': 2.5},
            },
            {
                'brand': self.brands[4],
                'title': 'Coffee Face Scrub - Get Ready With Me',
                'description': 'Looking for beauty and skincare creators for GRWM content featuring our Coffee Face Scrub.',
                'type': 'physical',
                'status': 'live',
                'estimated_value': 2500,
                'currency': 'INR',
                'quantity': 40,
                'quantity_remaining': 32,
                'rights_tier': 'standard',
                'exclusivity': 'none',
                'content_ask': {'types': ['reel', 'story'], 'count': 2, 'platforms': ['instagram']},
                'kpi_preferences': {'niches': ['beauty', 'skincare'], 'min_followers': 1000, 'min_engagement': 2.0},
            },
            {
                'brand': self.brands[0],
                'title': 'Winter Wardrobe Haul - Zara AW25',
                'description': 'Looking for fashion creators to do haul videos of our AW25 winter collection.',
                'type': 'physical',
                'status': 'live',
                'estimated_value': 15000,
                'currency': 'INR',
                'quantity': 10,
                'quantity_remaining': 7,
                'rights_tier': 'extended',
                'exclusivity': 'category_30',
                'content_ask': {'types': ['video', 'reel'], 'count': 3, 'platforms': ['instagram', 'youtube']},
                'kpi_preferences': {'niches': ['fashion', 'lifestyle'], 'min_followers': 20000, 'min_engagement': 3.0},
            },
        ]

        self.offers = []
        for data in offers_data:
            offer, created = Offer.objects.get_or_create(
                brand=data['brand'],
                title=data['title'],
                defaults={k: v for k, v in data.items() if k not in ['brand', 'title']}
            )
            self.offers.append(offer)

        self.stdout.write(f'  Created {len(self.offers)} offers')

    def _create_proposals(self):
        from apps.proposals.models import Proposal

        proposals_data = [
            {
                'offer': self.offers[0],
                'creator': self.creators[0],
                'pitch': 'Hi! I am a fashion and lifestyle creator with 45K engaged followers. Would love to showcase your summer collection in a try-on haul!',
                'deliverables': {'types': ['reel', 'story'], 'platforms': ['instagram'], 'count': 2},
                'timeline': date.today() + timedelta(days=14),
                'status': 'pending',
            },
            {
                'offer': self.offers[0],
                'creator': self.creators[6],
                'pitch': 'Fashion is my passion! 3 years of styling content, highly engaged audience. Would love to do a summer aesthetic reel for Zara!',
                'deliverables': {'types': ['reel', 'story'], 'platforms': ['instagram'], 'count': 2},
                'timeline': date.today() + timedelta(days=10),
                'status': 'accepted',
            },
            {
                'offer': self.offers[1],
                'creator': self.creators[2],
                'pitch': 'Beauty and skincare is my niche! Excited to feature Nykaa Naturals in my routine.',
                'deliverables': {'types': ['reel', 'story'], 'platforms': ['instagram'], 'count': 3},
                'timeline': date.today() + timedelta(days=12),
                'status': 'accepted',
            },
            {
                'offer': self.offers[3],
                'creator': self.creators[1],
                'pitch': 'Tech reviewer with 150K YouTube subscribers. My unboxing videos average 200K views!',
                'deliverables': {'types': ['video', 'reel'], 'platforms': ['youtube', 'instagram'], 'count': 2},
                'timeline': date.today() + timedelta(days=10),
                'status': 'pending',
            },
            {
                'offer': self.offers[2],
                'creator': self.creators[0],
                'pitch': 'I have been using Mamaearth for years! An honest review would resonate well with my audience.',
                'deliverables': {'types': ['reel', 'post'], 'platforms': ['instagram'], 'count': 2},
                'timeline': date.today() + timedelta(days=20),
                'status': 'countered',
            },
            {
                'offer': self.offers[4],
                'creator': self.creators[2],
                'pitch': 'GRWM is my specialty! Would love to feature the mCaffeine Coffee Scrub in my morning routine.',
                'deliverables': {'types': ['reel', 'story'], 'platforms': ['instagram'], 'count': 2},
                'timeline': date.today() + timedelta(days=8),
                'status': 'pending',
            },
        ]

        self.proposals = []
        for data in proposals_data:
            proposal, created = Proposal.objects.get_or_create(
                offer=data['offer'],
                creator=data['creator'],
                defaults={k: v for k, v in data.items() if k not in ['offer', 'creator']}
            )
            self.proposals.append(proposal)

        self.stdout.write(f'  Created {len(self.proposals)} proposals')

    def _create_deals(self):
        from apps.deals.models import Deal, Delivery, DealMessage

        self.deals = []
        for proposal in self.proposals:
            if proposal.status != 'accepted':
                continue
            if hasattr(proposal, 'accepted_deal'):
                self.deals.append(proposal.accepted_deal)
                continue

            deal_status = random.choice(['active', 'delivered', 'complete'])
            deal = Deal.objects.create(
                offer=proposal.offer,
                proposal=proposal,
                brand=proposal.offer.brand,
                creator=proposal.creator,
                agreed_terms={
                    'offer_title': proposal.offer.title,
                    'offer_type': proposal.offer.type,
                    'creator_deliverables': proposal.deliverables,
                    'timeline': str(proposal.timeline),
                    'rights_tier': proposal.offer.rights_tier,
                    'exclusivity': proposal.offer.exclusivity,
                },
                rights_tier=proposal.offer.rights_tier,
                raw_files_required=False,
                exclusivity=proposal.offer.exclusivity,
                deal_fee=999,
                currency='INR',
                status=deal_status,
                deadline=proposal.timeline,
            )
            self.deals.append(deal)

            DealMessage.objects.create(deal=deal, sender=deal.brand, body='Hi! Excited to work with you. Please let us know when you plan to post.')
            DealMessage.objects.create(deal=deal, sender=deal.creator, body='Thank you! I will send you a preview before posting.')
            DealMessage.objects.create(deal=deal, sender=deal.brand, body='Sounds great! Looking forward to the collaboration.')

            if deal_status in ['delivered', 'complete']:
                Delivery.objects.create(
                    deal=deal,
                    files=[],
                    post_urls=['https://www.instagram.com/p/mockpost123/'],
                    notes='Content posted as agreed.',
                    status='accepted' if deal_status == 'complete' else 'pending',
                )

        self.stdout.write(f'  Created {len(self.deals)} deals')

    def _create_drops(self):
        from apps.drops.models import DropsCampaign, DropsApplication

        campaigns_data = [
            {
                'offer': self.offers[0],
                'brand': self.brands[0],
                'name': 'Zara Summer Drop - Limited Slots',
                'goal': 'launch',
                'total_slots': 5,
                'status': 'live',
                'approval_mode': 'manual',
                'application_deadline': timezone.now() + timedelta(days=5),
            },
            {
                'offer': self.offers[3],
                'brand': self.brands[3],
                'name': 'boAt Product Drop - Tech Reviewers',
                'goal': 'review',
                'total_slots': 8,
                'status': 'live',
                'approval_mode': 'manual',
                'application_deadline': timezone.now() + timedelta(days=7),
            },
        ]

        self.campaigns = []
        for data in campaigns_data:
            campaign, created = DropsCampaign.objects.get_or_create(
                offer=data['offer'],
                brand=data['brand'],
                defaults={k: v for k, v in data.items() if k not in ['offer', 'brand']}
            )
            self.campaigns.append(campaign)
            if created:
                for creator in random.sample(self.creators, min(3, len(self.creators))):
                    DropsApplication.objects.get_or_create(
                        campaign=campaign,
                        creator=creator,
                        defaults={
                            'pitch': 'I would love to be part of this campaign! My audience would love this product.',
                            'status': random.choice(['pending', 'approved', 'declined']),
                        }
                    )

        self.stdout.write(f'  Created {len(self.campaigns)} drops campaigns')

    def _create_ratings(self):
        from apps.ratings.models import Rating

        count = 0
        for deal in self.deals:
            if deal.status == 'complete':
                Rating.objects.get_or_create(
                    deal=deal, rater=deal.brand, ratee=deal.creator,
                    defaults={
                        'stars': random.randint(4, 5),
                        'review_text': random.choice([
                            'Great collaboration! Content exceeded our expectations.',
                            'Very professional creator. Highly recommend.',
                            'Good work, would collaborate again.',
                        ]),
                        'published_at': timezone.now() - timedelta(days=random.randint(1, 10)),
                    }
                )
                Rating.objects.get_or_create(
                    deal=deal, rater=deal.creator, ratee=deal.brand,
                    defaults={
                        'stars': random.randint(4, 5),
                        'review_text': random.choice([
                            'Amazing brand to work with! Clear brief and great products.',
                            'Professional team. Would work with them again.',
                            'Good collab overall.',
                        ]),
                        'published_at': timezone.now() - timedelta(days=random.randint(1, 10)),
                    }
                )
                count += 2

        self.stdout.write(f'  Created {count} ratings')
