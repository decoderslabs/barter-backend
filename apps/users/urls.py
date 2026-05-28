from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),
    path('oauth/<str:platform>/url/', views.OAuthURLView.as_view(), name='oauth-url'),
    path('oauth/<str:platform>/callback/', views.OAuthCallbackView.as_view(), name='oauth-callback'),
    path('verify-domain/', views.VerifyDomainView.as_view(), name='verify-domain'),
]
