"""
Management command to seed demo data for Barter platform.
Creates 10 records for each major model with realistic fake data.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds demo data for Barter platform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding demo data...')

        # Create demo users
        self.create_users()
        self.create_offers()
        self.create_proposals()
        self.create_deals()
        self.create_drops()
        self.create_membership_tasks()
        self.create_wallet_transactions()

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))

    def create_users(self):
        from apps.users.models import BrandProfile, CreatorProfile, SocialAccount

        self.stdout.write('Creating demo users...')

        brand_users = []
        creator_users = []

        # Create 5 brands
        for i in range(1, 6):
            email = f'brand{i}@demo.com'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='demo123456',
                    role='brand',
                    name=f'Brand {i}',
                    username=f'brand{i}',
                    bio=f'Amazing brand number {i} looking for creators!',
                    location_city=random.choice(['Mumbai', 'Dubai', 'New York', 'London']),
                    location_country=random.choice(['IN', 'AE', 'US', 'UK']),
                    is_verified=random.choice([True, False])
                )
                BrandProfile.objects.create(
                    user=user,
                    company_name=f'Company {i} Ltd',
                    website=f'https://brand{i}.com',
                    industry=random.choice(['Fashion', 'Tech', 'Food', 'Beauty', 'Travel']),
                    domain_verified=random.choice([True, False])
                )
                brand_users.append(user)
                self.stdout.write(f'  Created brand: {user.username}')

        # Create 5 creators
        for i in range(1, 6):
            email = f'creator{i}@demo.com'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='demo123456',
                    role='creator',
                    name=f'Creator {i}',
                    username=f'creator{i}',
                    bio=f'Content creator specializing in lifestyle and travel.',
                    location_city=random.choice(['Mumbai', 'Dubai', 'New York', 'London']),
                    location_country=random.choice(['IN', 'AE', 'US', 'UK']),
                    is_verified=random.choice([True, False]),
                    barter_score=round(random.uniform(3.0, 9.5), 1)
                )
                tier = random.choice(['nano', 'micro', 'mid', 'macro', 'mega'])
                CreatorProfile.objects.create(
                    user=user,
                    niches=random.sample(['Fashion', 'Travel', 'Food', 'Tech', 'Beauty', 'Fitness'], 2),
                    content_types=random.sample(['Reels', 'Stories', 'Posts', 'Videos'], 2),
                    tier=tier
                )

                # Create social accounts
                platforms = ['instagram', 'tiktok', 'youtube', 'linkedin']
                followers_map = {
                    'nano': (1000, 8000),
                    'micro': (10000, 80000),
                    'mid': (100000, 400000),
                    'macro': (500000, 900000),
                    'mega': (1000000, 5000000)
                }

                for platform in random.sample(platforms, random.randint(2, 4)):
                    min_f, max_f = followers_map[tier]
                    followers = random.randint(min_f, max_f)
                    SocialAccount.objects.create(
                        user=user,
                        platform=platform,
                        handle=f'{user.username}_{platform}',
                        followers=followers,
                        engagement_rate=round(random.uniform(1.5, 8.0), 2),
                        avg_views=followers // random.randint(5, 20),
                        demographics={'age_18_24': 35, 'age_25_34': 45, 'top_city': 'Mumbai'},
                        last_synced=timezone.now()
                    )

                creator_users.append(user)
                self.stdout.write(f'  Created creator: {user.username} ({tier})')

        self.brand_users = brand_users
        self.creator_users = creator_users

    def create_offers(self):
        from apps.offers.models import Offer

        self.stdout.write('Creating demo offers...')

        offer_types = ['saas', 'physical', 'event_pass', 'experience', 'merchandise', 'course', 'gift_card']
        currencies = ['INR', 'AED', 'USD']
        rights_tiers = ['none', 'standard', 'extended', 'buyout']
        exclusivity = ['none', 'category_30', 'full_60']

        brands = User.objects.filter(role='brand')[:5]

        for i in range(10):
            brand = random.choice(brands)
            value = random.choice([2500, 5000, 10000, 25000, 50000, 100000])

            offer = Offer.objects.create(
                brand=brand,
                type=random.choice(offer_types),
                title=f'{random.choice(["Premium", "Exclusive", "Limited", "Special"])} {random.choice(["Product", "Service", "Experience", "Event"])} {i+1}',
                description=f'An amazing opportunity for creators! This is a demo offer with great value and exposure potential. Perfect for influencers in the {random.choice(["fashion", "tech", "lifestyle", "travel"])} niche.',
                estimated_value=value,
                currency=random.choice(currencies),
                quantity=random.randint(5, 20),
                status='live',
                content_ask={
                    'types': random.sample(['post', 'story', 'reel', 'video'], 2),
                    'platforms': random.sample(['instagram', 'tiktok', 'youtube'], 2),
                    'count': random.randint(1, 5)
                },
                kpi_preferences={
                    'min_followers': random.choice([1000, 10000, 50000]),
                    'min_engagement': random.uniform(1.0, 5.0),
                    'niches': random.sample(['Fashion', 'Travel', 'Tech'], 2)
                },
                rights_tier=random.choice(rights_tiers),
                raw_files_required=random.choice([True, False]),
                exclusivity=random.choice(exclusivity),
                images=[f'https://barter-storage.demo/offers/{i+1}/image1.jpg'],
                proposal_deadline=timezone.now() + timedelta(days=random.randint(7, 30)),
                shipping_required=random.choice([True, False])
            )
            self.stdout.write(f'  Created offer: {offer.title}')

    def create_proposals(self):
        from apps.offers.models import Offer
        from apps.proposals.models import Proposal

        self.stdout.write('Creating demo proposals...')

        offers = Offer.objects.filter(status='live')[:10]
        creators = User.objects.filter(role='creator')[:5]

        for i, offer in enumerate(offers):
            creator = random.choice(creators)

            # Check if proposal already exists
            if not Proposal.objects.filter(offer=offer, creator=creator).exists():
                proposal = Proposal.objects.create(
                    offer=offer,
                    creator=creator,
                    pitch=f"I'd love to work on this! My audience of {random.randint(10000, 50000)} followers would love your {offer.type}. I can create {random.randint(2, 5)} pieces of content across {random.choice(['Instagram', 'TikTok', 'YouTube'])}.",
                    deliverables={
                        'types': random.sample(['post', 'story', 'reel'], 2),
                        'platforms': random.sample(['instagram', 'tiktok'], 2),
                        'count': random.randint(2, 4),
                        'details': 'High-quality content with brand tags'
                    },
                    timeline=(timezone.now() + timedelta(days=random.randint(14, 45))).date(),
                    status=random.choice(['pending', 'countered', 'accepted', 'declined']),
                    round_number=random.randint(1, 3)
                )
                self.stdout.write(f'  Created proposal: {proposal.creator.username} -> {offer.title}')

    def create_deals(self):
        from apps.proposals.models import Proposal
        from apps.deals.models import Deal

        self.stdout.write('Creating demo deals...')

        accepted_proposals = Proposal.objects.filter(status='accepted')[:10]

        for proposal in accepted_proposals:
            if not hasattr(proposal, 'deal_link'):
                deal = Deal.objects.create(
                    offer=proposal.offer,
                    proposal=proposal,
                    brand=proposal.offer.brand,
                    creator=proposal.creator,
                    agreed_terms={
                        'offer_title': proposal.offer.title,
                        'offer_type': proposal.offer.type,
                        'offer_estimated_value': str(proposal.offer.estimated_value),
                        'creator_deliverables': proposal.deliverables,
                        'timeline': str(proposal.timeline)
                    },
                    rights_tier=proposal.offer.rights_tier,
                    raw_files_required=proposal.offer.raw_files_required,
                    exclusivity=proposal.offer.exclusivity,
                    deal_fee=self.calculate_deal_fee(proposal.offer.estimated_value, proposal.offer.currency),
                    currency=proposal.offer.currency,
                    status=random.choice(['active', 'delivered', 'complete']),
                    deadline=proposal.timeline
                )

                # Update proposal with deal reference
                proposal.deal = deal
                proposal.save()

                self.stdout.write(f'  Created deal: {deal.id} ({deal.status})')

    def calculate_deal_fee(self, value, currency):
        """Calculate deal fee based on value and currency"""
        if currency == 'INR':
            if value <= 5000:
                return 999
            elif value <= 15000:
                return 1499
            elif value <= 50000:
                return 1999
            else:
                return 2999
        elif currency == 'AED':
            if value <= 5000:
                return 44
            elif value <= 15000:
                return 66
            elif value <= 50000:
                return 88
            else:
                return 132
        else:  # USD
            if value <= 5000:
                return 12
            elif value <= 15000:
                return 18
            elif value <= 50000:
                return 24
            else:
                return 36

    def create_drops(self):
        from apps.drops.models import DropsCampaign, DropsApplication
        from apps.offers.models import Offer

        self.stdout.write('Creating demo drops campaigns...')

        offers = Offer.objects.filter(status='live')[:5]
        creators = User.objects.filter(role='creator')[:5]

        for i, offer in enumerate(offers):
            campaign = DropsCampaign.objects.create(
                brand=offer.brand,
                offer=offer,
                name=f'{offer.brand.username} Drops Campaign {i+1}',
                goal=random.choice(['awareness', 'launch', 'event_hype', 'review']),
                total_slots=random.randint(10, 50),
                approval_mode=random.choice(['auto', 'manual']),
                application_deadline=timezone.now() + timedelta(days=random.randint(14, 60)),
                status='live'
            )
            self.stdout.write(f'  Created drops: {campaign.name}')

            # Create applications
            for creator in random.sample(list(creators), random.randint(2, 4)):
                if not DropsApplication.objects.filter(campaign=campaign, creator=creator).exists():
                    DropsApplication.objects.create(
                        campaign=campaign,
                        creator=creator,
                        pitch=f'I would love to be part of this campaign! My content style aligns perfectly with your brand.',
                        status=random.choice(['pending', 'approved', 'declined'])
                    )

    def create_membership_tasks(self):
        from apps.membership.models import MembershipTask

        self.stdout.write('Creating demo membership tasks...')

        for i in range(10):
            task = MembershipTask.objects.create(
                brand_name=random.choice(['Nike', 'Adidas', 'Zara', 'Sephora', 'Apple', 'Samsung']),
                brand_logo_url=f'https://barter-storage.demo/brands/logo{i+1}.jpg',
                title=f'Create {random.choice(["Reel", "Story", "Post"])} featuring our {random.choice(["new product", "sale", "event"])}',
                platform=random.choice(['instagram', 'tiktok', 'open']),
                points_value=random.choice([10, 20, 30, 50, 100]),
                brief_richtext=f'Create engaging content for our brand. Use hashtags #{random.choice(["brand", "sale", "new"])}.',
                required_tags=[random.choice(['#sponsored', '#ad', '#partner')]],
                is_active=True,
                is_featured=random.choice([True, False]),
                available_to_tiers=random.sample(['nano', 'micro', 'mid', 'macro', 'mega'], 3),
                available_to_markets=random.sample(['IN', 'AE', 'US', 'UK'], 2)
            )
            self.stdout.write(f'  Created task: {task.title} ({task.points_value} pts)')

    def create_wallet_transactions(self):
        from apps.payments.models import Wallet

        self.stdout.write('Creating demo wallets...')

        creators = User.objects.filter(role='creator')[:5]

        for creator in creators:
            wallet, created = Wallet.objects.get_or_create(user=creator)
            if created or wallet.balance == 0:
                # Add some points
                points = random.randint(50, 500)
                wallet.add_points(
                    points,
                    description='Welcome bonus and task rewards',
                    source='demo_seed'
                )
                self.stdout.write(f'  Created wallet for {creator.username}: {points} pts')
