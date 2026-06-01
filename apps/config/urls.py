from django.urls import path
from .views import OnboardingConfigView

urlpatterns = [
    path('onboarding/', OnboardingConfigView.as_view(), name='onboarding-config'),
]
