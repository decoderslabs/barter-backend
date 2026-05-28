from django.urls import path
from . import views

urlpatterns = [
    path('', views.DropsListCreateView.as_view(), name='drops-list-create'),
    path('<uuid:id>/', views.DropsDetailView.as_view(), name='drops-detail'),
    path('<uuid:id>/apply/', views.ApplyToDropsView.as_view(), name='drops-apply'),
    path('<uuid:id>/applications/', views.DropsApplicationsListView.as_view(), name='drops-applications'),
    path('<uuid:id>/applications/<uuid:app_id>/approve/', views.ApproveApplicationView.as_view(), name='drops-approve'),
    path('<uuid:id>/applications/<uuid:app_id>/decline/', views.DeclineApplicationView.as_view(), name='drops-decline'),
    path('<uuid:id>/shipping-export/', views.ShippingExportView.as_view(), name='drops-shipping-export'),
]
