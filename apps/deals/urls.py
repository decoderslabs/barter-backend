from django.urls import path
from . import views

urlpatterns = [
    path('', views.DealListView.as_view(), name='deal-list'),
    path('<uuid:id>/', views.DealDetailView.as_view(), name='deal-detail'),
    path('<uuid:id>/ship/', views.ShipDealView.as_view(), name='deal-ship'),
    path('<uuid:id>/confirm-receipt/', views.ConfirmReceiptView.as_view(), name='deal-confirm-receipt'),
    path('<uuid:id>/deliver/', views.DeliverContentView.as_view(), name='deal-deliver'),
    path('<uuid:id>/approve/', views.ApproveDeliveryView.as_view(), name='deal-approve'),
    path('<uuid:id>/request-revision/', views.RequestRevisionView.as_view(), name='deal-revision'),
    path('<uuid:id>/complete/', views.CompleteDealView.as_view(), name='deal-complete'),
    path('<uuid:id>/dispute/', views.DisputeDealView.as_view(), name='deal-dispute'),
    path('<uuid:id>/messages/', views.DealMessageListView.as_view(), name='deal-messages'),
    path('<uuid:id>/messages/send/', views.DealMessageCreateView.as_view(), name='deal-message-create'),
]
