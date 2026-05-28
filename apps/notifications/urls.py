from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<uuid:id>/read/', views.MarkNotificationReadView.as_view(), name='notification-read'),
    path('read-all/', views.MarkAllNotificationsReadView.as_view(), name='notifications-read-all'),
]
