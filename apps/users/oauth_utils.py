"""
OAuth utilities for social media platforms.
Real implementations for Instagram, TikTok, and LinkedIn.
"""
import requests
from django.conf import settings


class InstagramOAuth:
    """Instagram Basic Display and Graph API OAuth"""

    AUTH_URL = "https://api.instagram.com/oauth/authorize"
    TOKEN_URL = "https://api.instagram.com/oauth/access_token"
    GRAPH_API_BASE = "https://graph.instagram.com"

    @classmethod
    def get_auth_url(cls, redirect_uri, state=""):
        """Get Instagram OAuth authorization URL"""
        params = {
            'client_id': settings.INSTAGRAM_APP_ID,
            'redirect_uri': redirect_uri,
            'scope': 'instagram_basic,pages_read_engagement',
            'response_type': 'code',
            'state': state
        }
        url = f"{cls.AUTH_URL}?{requests.compat.urlencode(params)}"
        return url

    @classmethod
    def exchange_code(cls, code, redirect_uri):
        """Exchange authorization code for access token"""
        data = {
            'client_id': settings.INSTAGRAM_APP_ID,
            'client_secret': settings.INSTAGRAM_APP_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code
        }
        response = requests.post(cls.TOKEN_URL, data=data)
        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_user_profile(cls, access_token):
        """Get Instagram user profile with follower count"""
        url = f"{cls.GRAPH_API_BASE}/me"
        params = {
            'fields': 'id,username,account_type,media_count',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_followers(cls, access_token):
        """Get follower count (requires business/creator account)"""
        url = f"{cls.GRAPH_API_BASE}/me"
        params = {
            'fields': 'followers_count',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('followers_count', 0)
        return 0

    @classmethod
    def get_recent_media(cls, access_token, limit=12):
        """Get recent media for engagement calculation"""
        url = f"{cls.GRAPH_API_BASE}/me/media"
        params = {
            'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count',
            'limit': limit,
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('data', [])
        return []

    @classmethod
    def calculate_engagement_rate(cls, access_token, followers):
        """Calculate engagement rate from recent posts"""
        media = cls.get_recent_media(access_token)
        if not media or followers == 0:
            return 0.0

        total_engagement = 0
        for post in media:
            likes = post.get('like_count', 0)
            comments = post.get('comments_count', 0)
            total_engagement += likes + comments

        avg_engagement = total_engagement / len(media)
        engagement_rate = (avg_engagement / followers) * 100
        return round(engagement_rate, 2)


class TikTokOAuth:
    """TikTok for Developers OAuth"""

    AUTH_URL = "https://open-api.tiktok.com/platform/oauth/connect/"
    TOKEN_URL = "https://open-api.tiktok.com/oauth/access_token/"
    API_BASE = "https://open-api.tiktok.com"

    @classmethod
    def get_auth_url(cls, redirect_uri, state=""):
        """Get TikTok OAuth authorization URL"""
        params = {
            'client_key': settings.TIKTOK_CLIENT_KEY,
            'redirect_uri': redirect_uri,
            'scope': 'user.info.basic,video.list',
            'response_type': 'code',
            'state': state
        }
        url = f"{cls.AUTH_URL}?{requests.compat.urlencode(params)}"
        return url

    @classmethod
    def exchange_code(cls, code):
        """Exchange authorization code for access token"""
        data = {
            'client_key': settings.TIKTOK_CLIENT_KEY,
            'client_secret': settings.TIKTOK_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(cls.TOKEN_URL, json=data)
        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_user_info(cls, access_token, open_id):
        """Get TikTok user info including follower count"""
        url = f"{cls.API_BASE}/user/info/"
        params = {
            'access_token': access_token,
            'open_id': open_id,
            'fields': 'open_id,union_id,avatar_url,display_name,follower_count,following_count,like_count,video_count'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                return data['data']
        return None

    @classmethod
    def get_video_list(cls, access_token, open_id, max_count=20):
        """Get user's videos for view count calculation"""
        url = f"{cls.API_BASE}/video/list/"
        params = {
            'access_token': access_token,
            'open_id': open_id,
            'max_count': max_count,
            'fields': 'id,title,video_description,view_count,like_count,comment_count,share_count'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('list', [])
        return []

    @classmethod
    def calculate_avg_views(cls, access_token, open_id):
        """Calculate average views from recent videos"""
        videos = cls.get_video_list(access_token, open_id, max_count=20)
        if not videos:
            return 0

        total_views = sum(v.get('view_count', 0) for v in videos)
        return total_views // len(videos)


class LinkedInOAuth:
    """LinkedIn OAuth 2.0"""

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_BASE = "https://api.linkedin.com/v2"

    @classmethod
    def get_auth_url(cls, redirect_uri, state=""):
        """Get LinkedIn OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'r_liteprofile r_emailaddress r_organization_social',
            'state': state
        }
        url = f"{cls.AUTH_URL}?{requests.compat.urlencode(params)}"
        return url

    @classmethod
    def exchange_code(cls, code, redirect_uri):
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET,
            'redirect_uri': redirect_uri
        }
        response = requests.post(cls.TOKEN_URL, data=data)
        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_profile(cls, access_token):
        """Get LinkedIn user profile"""
        url = f"{cls.API_BASE}/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_email(cls, access_token):
        """Get LinkedIn user email"""
        url = f"{cls.API_BASE}/emailAddress?q=members&projection=(elements*(handle~))"
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            if elements:
                return elements[0].get('handle~', {}).get('emailAddress')
        return None

    @classmethod
    def get_organization_followers(cls, access_token, organization_urn):
        """Get organization page follower count"""
        url = f"{cls.API_BASE}/networkSizes/{organization_urn}"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'edgeType': 'CompanyFollowedByMember'}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('firstDegreeSize', 0)
        return 0


class YouTubeOAuth:
    """YouTube Data API OAuth"""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_BASE = "https://www.googleapis.com/youtube/v3"

    @classmethod
    def get_auth_url(cls, redirect_uri, state=""):
        """Get YouTube OAuth authorization URL"""
        scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/yt-analytics.readonly'
        ]
        params = {
            'client_id': settings.YOUTUBE_CLIENT_ID if hasattr(settings, 'YOUTUBE_CLIENT_ID') else '',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'state': state,
            'include_granted_scopes': 'true'
        }
        url = f"{cls.AUTH_URL}?{requests.compat.urlencode(params)}"
        return url

    @classmethod
    def exchange_code(cls, code, redirect_uri):
        """Exchange authorization code for access token"""
        data = {
            'code': code,
            'client_id': settings.YOUTUBE_CLIENT_ID if hasattr(settings, 'YOUTUBE_CLIENT_ID') else '',
            'client_secret': settings.YOUTUBE_CLIENT_SECRET if hasattr(settings, 'YOUTUBE_CLIENT_SECRET') else '',
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        response = requests.post(cls.TOKEN_URL, data=data)
        if response.status_code == 200:
            return response.json()
        return None

    @classmethod
    def get_channel_info(cls, access_token):
        """Get YouTube channel info including subscriber count"""
        url = f"{cls.API_BASE}/channels"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'part': 'statistics,snippet,contentDetails',
            'mine': 'true'
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items:
                return items[0]
        return None

    @classmethod
    def get_recent_videos(cls, access_token, channel_id, max_results=20):
        """Get recent videos for view count calculation"""
        url = f"{cls.API_BASE}/search"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'maxResults': max_results,
            'order': 'date',
            'type': 'video'
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        return []

    @classmethod
    def get_video_stats(cls, access_token, video_ids):
        """Get video statistics (views, likes, comments)"""
        url = f"{cls.API_BASE}/videos"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'part': 'statistics',
            'id': ','.join(video_ids)
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        return []

    @classmethod
    def calculate_avg_views(cls, access_token, channel_id):
        """Calculate average views from recent videos"""
        videos = cls.get_recent_videos(access_token, channel_id, max_results=20)
        if not videos:
            return 0

        video_ids = [v['id']['videoId'] for v in videos]
        if not video_ids:
            return 0

        stats = cls.get_video_stats(access_token, video_ids)
        total_views = sum(int(s['statistics'].get('viewCount', 0)) for s in stats)
        return total_views // len(stats) if stats else 0


# OAuth URL generator helper
def get_oauth_url(platform, redirect_uri, state=""):
    """Get OAuth URL for any supported platform"""
    platforms = {
        'instagram': InstagramOAuth,
        'tiktok': TikTokOAuth,
        'linkedin': LinkedInOAuth,
        'youtube': YouTubeOAuth,
    }

    oauth_class = platforms.get(platform)
    if oauth_class:
        return oauth_class.get_auth_url(redirect_uri, state)
    return None


def exchange_oauth_code(platform, code, redirect_uri=None):
    """Exchange OAuth code for tokens for any supported platform"""
    platforms = {
        'instagram': InstagramOAuth,
        'tiktok': TikTokOAuth,
        'linkedin': LinkedInOAuth,
        'youtube': YouTubeOAuth,
    }

    oauth_class = platforms.get(platform)
    if oauth_class:
        if platform in ['instagram', 'linkedin', 'youtube'] and redirect_uri:
            return oauth_class.exchange_code(code, redirect_uri)
        return oauth_class.exchange_code(code)
    return None
