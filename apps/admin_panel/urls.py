from django.urls import path
from . import views

urlpatterns = [
    path('deals/', views.DealsAnalyticsView.as_view(), name='deals-analytics'),
    path('creators/', views.CreatorsAnalyticsView.as_view(), name='creators-analytics'),
    path('content/', views.ContentAnalyticsView.as_view(), name='content-analytics'),
]
