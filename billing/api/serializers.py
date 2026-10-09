from rest_framework import serializers

from billing.models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "id",
            "code",
            "name",
            "description",
            "price_minor",
            "currency",
            "billing_interval",
            "trial_days",
            "sort_order",
        )
        read_only_fields = fields


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = (
            "id",
            "plan",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "cancelled_at",
            "created_at",
        )
        read_only_fields = fields
