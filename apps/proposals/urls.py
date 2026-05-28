from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProposalListView.as_view(), name='proposal-list'),
    path('<uuid:id>/', views.ProposalDetailView.as_view(), name='proposal-detail'),
    path('<uuid:id>/counter/', views.CounterProposalView.as_view(), name='proposal-counter'),
    path('<uuid:id>/accept/', views.AcceptProposalView.as_view(), name='proposal-accept'),
    path('<uuid:id>/decline/', views.DeclineProposalView.as_view(), name='proposal-decline'),
]
