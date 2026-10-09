from rest_framework import serializers

from accounts.api.public_serializers import UserPublicSerializer
from accounts.models import User
from platformcfg.models import FeatureFlag
from safety.models import AdminAuditLog


class AdminUserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="username", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "display_name",
            "account_status",
            "verification_status",
            "date_joined",
        )
        read_only_fields = fields


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = (
            "id",
            "key",
            "enabled",
            "description",
            "rules",
            "rollout_percentage",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "key", "created_at")


class AdminAuditLogSerializer(serializers.ModelSerializer):
    actor = UserPublicSerializer(read_only=True)

    class Meta:
        model = AdminAuditLog
        fields = (
            "id",
            "actor",
            "action",
            "target_type",
            "target_id",
            "ip_address",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
