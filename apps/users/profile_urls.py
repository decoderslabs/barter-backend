from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.MeView.as_view(), name='me'),
    path('<uuid:id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('me/social-accounts/', views.SocialAccountListCreateView.as_view(), name='social-accounts'),
    path('me/social-accounts/<str:platform>/', views.SocialAccountDeleteView.as_view(), name='social-account-delete'),
    path('me/brand-profile/', views.BrandProfileUpdateView.as_view(), name='brand-profile'),
    path('me/creator-profile/', views.CreatorProfileUpdateView.as_view(), name='creator-profile'),
]
