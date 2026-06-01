from rest_framework import serializers
from .models import MembershipTask, MembershipTaskSubmission, CreatorMembership


class MembershipTaskSerializer(serializers.ModelSerializer):
    points = serializers.IntegerField(source='points_value', read_only=True)
    is_available = serializers.SerializerMethodField()
    brief = serializers.SerializerMethodField()

    class Meta:
        model = MembershipTask
        fields = [
            'id', 'brand_name', 'brand_logo_url', 'title', 'platform',
            'points_value', 'points', 'brief_richtext', 'brief', 'required_tags',
            'is_featured', 'is_available', 'available_again_on',
            'available_to_tiers', 'available_to_markets', 'created_at'
        ]

    def get_is_available(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            return obj.is_available_for_user(user)
        return obj.is_active

    def get_brief(self, obj):
        # If brief dict is empty, construct from brief_richtext
        if obj.brief:
            return obj.brief
        return {
            'what_to_create': obj.brief_richtext,
            'key_messages': [],
            'donts': [],
            'required_tags': obj.required_tags,
            'example_url': None
        }


class MembershipTaskBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipTask
        fields = ['id', 'brand_name', 'brand_logo_url', 'title', 'brief_richtext', 'required_tags']


class MembershipTaskSubmissionSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_brand = serializers.CharField(source='task.brand_name', read_only=True)
    task_points = serializers.IntegerField(source='task.points_value', read_only=True)

    class Meta:
        model = MembershipTaskSubmission
        fields = [
            'id', 'task', 'task_title', 'task_brand', 'task_points',
            'post_url', 'note', 'status', 'rejection_reason',
            'points_awarded', 'submitted_at', 'reviewed_at'
        ]


class MembershipTaskSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipTaskSubmission
        fields = ['task', 'post_url', 'note']

    def validate_task(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This task is not active")

        # Check tier eligibility
        user = self.context['request'].user
        if hasattr(user, 'creator_profile'):
            user_tier = user.creator_profile.tier
            if value.available_to_tiers and user_tier not in value.available_to_tiers:
                raise serializers.ValidationError("Your tier is not eligible for this task")

        # Check market eligibility
        if value.available_to_markets and user.location_country:
            user_market = user.location_country.upper()
            if user_market not in value.available_to_markets:
                raise serializers.ValidationError("Your market is not eligible for this task")

        return value

    def validate(self, data):
        user = self.context['request'].user

        # Check if already submitted
        existing = MembershipTaskSubmission.objects.filter(
            creator=user,
            task=data['task']
        ).first()
        if existing:
            raise serializers.ValidationError("You have already submitted for this task")

        # Check membership period
        if hasattr(user, 'membership'):
            membership = user.membership
            if not membership.can_submit_task(str(data['task'].id)):
                raise serializers.ValidationError("Task already submitted this period")

        return data

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        submission = super().create(validated_data)

        # Record in membership
        if hasattr(submission.creator, 'membership'):
            submission.creator.membership.record_task_submission(str(submission.task.id))

        return submission


class MembershipStatusSerializer(serializers.ModelSerializer):
    pro_days_remaining = serializers.SerializerMethodField()
    points_to_next_milestone = serializers.SerializerMethodField()
    period_label = serializers.SerializerMethodField()
    period_task_limit = serializers.SerializerMethodField()
    completed_this_period = serializers.SerializerMethodField()
    next_milestone_label = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    class Meta:
        model = CreatorMembership
        fields = [
            'total_points', 'pro_active', 'pro_expires_at',
            'pro_days_remaining', 'tier', 'tasks_this_period', 'period_reset_at',
            'pending_verification', 'points_to_next_milestone', 'period_label',
            'period_task_limit', 'completed_this_period', 'next_milestone_label', 'history'
        ]

    def get_pro_days_remaining(self, obj):
        if obj.pro_expires_at:
            from django.utils import timezone
            delta = obj.pro_expires_at - timezone.now()
            return max(0, delta.days)
        return 0

    def get_points_to_next_milestone(self, obj):
        milestones = [(50, 1), (100, 2), (150, 3), (250, 6), (400, 12)]
        for points_needed, _ in milestones:
            if obj.total_points < points_needed:
                return points_needed - obj.total_points
        return 0

    def get_period_label(self, obj):
        return 'month'

    def get_period_task_limit(self, obj):
        return 3

    def get_completed_this_period(self, obj):
        return len(obj.tasks_this_period)

    def get_next_milestone_label(self, obj):
        milestones = [(50, '1 month Pro'), (100, '2 months Pro'), (150, '3 months Pro'),
                     (250, '6 months Pro'), (400, '12 months Pro')]
        for points_needed, label in milestones:
            if obj.total_points < points_needed:
                return label
        return 'Max tier reached'

    def get_history(self, obj):
        return obj.points_history


class MembershipReviewSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_name = serializers.CharField(source='creator.name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)

    class Meta:
        model = MembershipTaskSubmission
        fields = [
            'id', 'creator', 'creator_username', 'creator_name',
            'task', 'task_title', 'post_url', 'note', 'status',
            'points_awarded', 'submitted_at'
        ]


class MembershipReviewActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected', 'resubmit_requested'])
    points_awarded = serializers.IntegerField(required=False, min_value=0)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
