from django.urls import path
from .views import BrandDashboardView, BrandInboxView

urlpatterns = [
    path('dashboard/', BrandDashboardView.as_view(), name='brand-dashboard'),
    path('inbox/', BrandInboxView.as_view(), name='brand-inbox'),
]
