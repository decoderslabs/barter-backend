from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.MembershipTaskListView.as_view(), name='membership-tasks'),
    path('tasks/<uuid:id>/brief/', views.MembershipTaskBriefView.as_view(), name='membership-task-brief'),
    path('submissions/', views.MembershipSubmissionCreateView.as_view(), name='membership-submit'),
    path('status/', views.MembershipStatusView.as_view(), name='membership-status'),
    path('admin/queue/', views.MembershipReviewQueueView.as_view(), name='membership-queue'),
    path('admin/submissions/<uuid:id>/review/', views.MembershipReviewActionView.as_view(), name='membership-review'),
]
