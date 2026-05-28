from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:id>/contract/', views.ContractPDFView.as_view(), name='contract-get'),
]
