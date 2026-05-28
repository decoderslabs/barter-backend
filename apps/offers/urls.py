from django.urls import path
from . import views
from apps.proposals.views import ProposalCreateView

urlpatterns = [
    path('', views.OfferListCreateView.as_view(), name='offer-list-create'),
    path('<uuid:id>/', views.OfferDetailView.as_view(), name='offer-detail'),
    path('<uuid:id>/value-engine/', views.ValueEngineView.as_view(), name='value-engine'),
    path('<uuid:id>/proposals/', ProposalCreateView.as_view(), name='proposal-create'),
    path('my/', views.MyOffersView.as_view(), name='my-offers'),
]
