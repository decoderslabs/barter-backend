from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import SocialAccount, BrandProfile, CreatorProfile
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserMeSerializer,
    SocialAccountSerializer, SocialAccountCreateSerializer,
    BrandProfileSerializer, BrandProfileCreateSerializer,
    CreatorProfileSerializer, CreatorProfileCreateSerializer,
    CreatorListSerializer,
)

User = get_user_model()


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST'), name='post')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.role in ['brand', 'both']:
            BrandProfile.objects.create(user=user)
        if user.role in ['creator', 'both']:
            CreatorProfile.objects.create(user=user)

        return Response({
            'user': UserSerializer(user).data,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='post')
class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Logged out successfully'})


class TokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserMeSerializer(user).data)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'


class CreatorListView(generics.ListAPIView):
    """Browse creators for brand discovery."""
    serializer_class = CreatorListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.filter(role__in=['creator', 'both']).select_related(
            'creator_profile'
        ).prefetch_related('social_accounts')

        niche = self.request.query_params.get('niche')
        if niche:
            queryset = queryset.filter(creator_profile__niches__contains=[niche])

        tier = self.request.query_params.get('tier')
        if tier:
            queryset = queryset.filter(creator_profile__tier=tier.lower())

        return queryset.order_by('-barter_score', '-created_at')


class SocialAccountListCreateView(generics.ListCreateAPIView):
    serializer_class = SocialAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SocialAccount.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SocialAccountCreateSerializer
        return SocialAccountSerializer

    def perform_create(self, serializer):
        account = serializer.save(user=self.request.user)
        if self.request.user.role in ['creator', 'both']:
            self.request.user.creator_profile.calculate_tier()
        return account


class SocialAccountDeleteView(generics.DestroyAPIView):
    serializer_class = SocialAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'platform'

    def get_queryset(self):
        return SocialAccount.objects.filter(user=self.request.user)

    def get_object(self):
        platform = self.kwargs.get('platform')
        return SocialAccount.objects.get(user=self.request.user, platform=platform)


class BrandProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = BrandProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = BrandProfile.objects.get_or_create(user=self.request.user)
        return profile


class CreatorProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = CreatorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = CreatorProfile.objects.get_or_create(user=self.request.user)
        return profile


class VerifyDomainView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role not in ['brand', 'both']:
            return Response({'error': 'Only brands can verify domains'}, status=403)

        website = request.data.get('website')
        if not website:
            return Response({'error': 'Website URL required'}, status=400)

        brand_profile = request.user.brand_profile
        brand_profile.website = website
        brand_profile.domain_verified = True
        brand_profile.save()

        return Response({
            'message': 'Domain verified successfully',
            'domain_verified': True
        })


class OAuthURLView(APIView):
    """Get OAuth URL for a platform"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, platform):
        from .oauth_utils import get_oauth_url

        allowed_platforms = ['instagram', 'tiktok', 'youtube', 'linkedin']
        if platform not in allowed_platforms:
            return Response({'error': 'Invalid platform'}, status=400)

        redirect_uri = request.query_params.get('redirect_uri', 'http://localhost:3000/oauth/callback')
        state = request.query_params.get('state', '')

        auth_url = get_oauth_url(platform, redirect_uri, state)
        if not auth_url:
            return Response({'error': f'{platform} OAuth not configured'}, status=500)

        return Response({
            'platform': platform,
            'auth_url': auth_url
        })


class OAuthCallbackView(APIView):
    """Handle OAuth callback and connect social account"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, platform):
        from .oauth_utils import (
            exchange_oauth_code, InstagramOAuth, TikTokOAuth,
            LinkedInOAuth, YouTubeOAuth
        )
        from django.utils import timezone

        allowed_platforms = ['instagram', 'tiktok', 'youtube', 'linkedin']
        if platform not in allowed_platforms:
            return Response({'error': 'Invalid platform'}, status=400)

        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri', 'http://localhost:3000/oauth/callback')

        if not code:
            return Response({'error': 'OAuth code required'}, status=400)

        # Exchange code for tokens
        token_data = exchange_oauth_code(platform, code, redirect_uri)
        if not token_data:
            return Response({'error': 'Failed to exchange OAuth code'}, status=400)

        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token', '')

        # Get platform-specific user info
        handle = ''
        followers = 0
        engagement_rate = 0.0
        avg_views = 0
        demographics = {}

        try:
            if platform == 'instagram':
                profile = InstagramOAuth.get_user_profile(access_token)
                if profile:
                    handle = profile.get('username', '')
                    followers = InstagramOAuth.get_followers(access_token)
                    engagement_rate = InstagramOAuth.calculate_engagement_rate(access_token, followers)

            elif platform == 'tiktok':
                open_id = token_data.get('open_id', '')
                user_info = TikTokOAuth.get_user_info(access_token, open_id)
                if user_info:
                    handle = user_info.get('display_name', '')
                    followers = user_info.get('follower_count', 0)
                    avg_views = TikTokOAuth.calculate_avg_views(access_token, open_id)

            elif platform == 'linkedin':
                profile = LinkedInOAuth.get_profile(access_token)
                if profile:
                    handle = profile.get('localizedFirstName', '') + ' ' + profile.get('localizedLastName', '')
                    # LinkedIn personal profiles don't show followers easily
                    followers = 0

            elif platform == 'youtube':
                channel = YouTubeOAuth.get_channel_info(access_token)
                if channel:
                    snippet = channel.get('snippet', {})
                    statistics = channel.get('statistics', {})
                    handle = snippet.get('title', '')
                    followers = statistics.get('subscriberCount', 0)
                    channel_id = channel.get('id', '')
                    avg_views = YouTubeOAuth.calculate_avg_views(access_token, channel_id)

        except Exception as e:
            # Log error but continue - we have the tokens at least
            print(f"Error fetching {platform} profile: {e}")

        account, created = SocialAccount.objects.update_or_create(
            user=request.user,
            platform=platform,
            defaults={
                'handle': handle,
                'followers': followers,
                'engagement_rate': engagement_rate,
                'avg_views': avg_views,
                'demographics': demographics,
                'last_synced': timezone.now(),
            }
        )
        account.set_access_token(access_token)
        if refresh_token:
            account.refresh_token = refresh_token
        account.save()

        if request.user.role in ['creator', 'both']:
            request.user.creator_profile.calculate_tier()

        return Response({
            'message': f'{platform} account connected',
            'account': SocialAccountSerializer(account).data
        })
