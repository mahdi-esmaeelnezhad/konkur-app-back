from rest_framework import serializers

from accounts.api.public_serializers import UserPublicSerializer
from messaging.models import Conversation, Message, Notification, UserNotificationSetting


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = (
            "id",
            "kind",
            "title",
            "last_message_at",
            "created_at",
        )
        read_only_fields = fields


class ConversationCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class MessageSerializer(serializers.ModelSerializer):
    sender = UserPublicSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "body",
            "reply_to",
            "edited_at",
            "created_at",
        )
        read_only_fields = ("id", "sender", "edited_at", "created_at")


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("body", "reply_to")


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "notification_type",
            "title",
            "body",
            "payload",
            "priority",
            "read_at",
            "created_at",
        )
        read_only_fields = fields


class UserNotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSetting
        fields = (
            "quiet_hours_start",
            "quiet_hours_end",
            "timezone",
            "marketing_opt_in",
            "digest_enabled",
            "preferences",
        )
