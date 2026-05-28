from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MembershipTask, MembershipTaskSubmission, CreatorMembership
from .serializers import (
    MembershipTaskSerializer, MembershipTaskBriefSerializer,
    MembershipTaskSubmissionSerializer, MembershipTaskSubmissionCreateSerializer,
    MembershipStatusSerializer, MembershipReviewSerializer, MembershipReviewActionSerializer
)
from apps.notifications.utils import send_notification


class IsCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['creator', 'both']


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff


class MembershipTaskListView(generics.ListAPIView):
    serializer_class = MembershipTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = MembershipTask.objects.filter(is_active=True)

        user = self.request.user
        if hasattr(user, 'creator_profile'):
            user_tier = user.creator_profile.tier
            queryset = queryset.filter(available_to_tiers__contains=[user_tier])

        if user.location_country:
            user_market = user.location_country.upper()
            queryset = queryset.filter(available_to_markets__contains=[user_market])

        return queryset.order_by('-is_featured', '-created_at')


class MembershipTaskBriefView(generics.RetrieveAPIView):
    queryset = MembershipTask.objects.all()
    serializer_class = MembershipTaskBriefSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]


class MembershipSubmissionCreateView(generics.CreateAPIView):
    serializer_class = MembershipTaskSubmissionCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def perform_create(self, serializer):
        submission = serializer.save()

        # Notify admins (simplified - in production, notify specific reviewers)
        send_notification(
            user_id=submission.creator.id,
            notification_type='membership_submitted',
            title='Task Submitted',
            body=f'Your submission for {submission.task.title} is under review',
            deep_link=f'/membership/submissions'
        )

        return submission


class MembershipStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCreator]

    def get(self, request):
        membership, created = CreatorMembership.objects.get_or_create(
            creator=request.user,
            defaults={'tier': request.user.creator_profile.tier if hasattr(request.user, 'creator_profile') else 'nano'}
        )

        # Check and update pro status
        membership.check_pro_status()

        return Response(MembershipStatusSerializer(membership).data)


class MembershipReviewQueueView(generics.ListAPIView):
    serializer_class = MembershipReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return MembershipTaskSubmission.objects.filter(
            status='pending'
        ).select_related('creator', 'task').order_by('submitted_at')


class MembershipReviewActionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, id):
        try:
            submission = MembershipTaskSubmission.objects.get(id=id)
        except MembershipTaskSubmission.DoesNotExist:
            return Response({'error': 'Submission not found'}, status=404)

        serializer = MembershipReviewActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        new_status = serializer.validated_data['status']
        submission.status = new_status
        submission.reviewer = request.user
        submission.reviewed_at = timezone.now()

        if new_status == 'approved':
            points = serializer.validated_data.get('points_awarded', submission.task.points_value)
            submission.points_awarded = points

            # Add points to creator membership
            if hasattr(submission.creator, 'membership'):
                submission.creator.membership.add_points(points)

            send_notification(
                user_id=submission.creator.id,
                notification_type='membership_approved',
                title='Task Approved!',
                body=f'Your submission for {submission.task.title} was approved. +{points} points!',
                deep_link=f'/membership/status'
            )
        elif new_status == 'rejected':
            submission.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            send_notification(
                user_id=submission.creator.id,
                notification_type='membership_rejected',
                title='Task Rejected',
                body=f'Your submission for {submission.task.title} was not approved',
                deep_link=f'/membership/submissions'
            )
        else:  # resubmit_requested
            send_notification(
                user_id=submission.creator.id,
                notification_type='membership_resubmit',
                title='Revision Requested',
                body=f'Please revise your submission for {submission.task.title}',
                deep_link=f'/membership/submissions'
            )

        submission.save()
        return Response(MembershipReviewSerializer(submission).data)


from django.utils import timezone
