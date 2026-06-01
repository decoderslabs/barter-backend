from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class OnboardingConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            "niches": ["Beauty", "Skincare", "Fashion", "Lifestyle", "Tech", "Food", "Travel", "Fitness"],
            "interests": ["UGC", "Editorial", "Product Reviews", "Lifestyle", "Educational", "Entertainment"],
            "content_types": [
                "Instagram Reels",
                "Instagram Stories",
                "Instagram Carousels",
                "TikTok Videos",
                "YouTube Shorts",
                "YouTube Long-form"
            ],
            "platforms": [
                {"id": "instagram", "label": "Instagram", "color": "#E1306C"},
                {"id": "tiktok", "label": "TikTok", "color": "#000000"},
                {"id": "youtube", "label": "YouTube", "color": "#FF0000"},
                {"id": "linkedin", "label": "LinkedIn", "color": "#0077B5"}
            ],
            "follower_ranges": [
                {"id": "nano", "label": "Nano", "range": "1K–10K"},
                {"id": "micro", "label": "Micro", "range": "10K–50K"},
                {"id": "mid", "label": "Mid", "range": "50K–100K"},
                {"id": "macro", "label": "Macro", "range": "100K–500K"},
                {"id": "mega", "label": "Mega", "range": "500K+"}
            ],
            "creator_profile_defaults": {
                "suggested_name": "Elena Rossi",
                "suggested_handle": "elenarossi",
                "suggested_bio": "Fashion & lifestyle content creator based in Milan. Collaborating with brands I love.",
                "suggested_location": "Milan, Italy",
                "default_avatar": "https://ui-avatars.com/api/?name=Elena+Rossi&background=random"
            },
            "brand_profile_defaults": {
                "avatar_url": "https://ui-avatars.com/api/?name=Aura+Collective&background=random",
                "suggested_company_name": "Aura Collective",
                "suggested_industry": "Beauty & Wellness"
            }
        }
        return Response(data)

