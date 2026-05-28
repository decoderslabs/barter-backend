from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:id>/rate/', views.RateDealView.as_view(), name='rate-deal'),
]
