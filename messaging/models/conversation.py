from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ConversationKind(models.TextChoices):
    DIRECT = "direct", "Direct"
    GROUP = "group", "Group"
    SUPPORT = "support", "Support"


class Conversation(TimeStampedModel):
    kind = models.CharField(
        max_length=32,
        choices=ConversationKind.choices,
        default=ConversationKind.DIRECT,
        db_index=True,
    )
    title = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations_created",
    )
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "last_message_at"]),
        ]


class ConversationParticipantRole(models.TextChoices):
    MEMBER = "member", "Member"
    ADMIN = "admin", "Admin"


class ConversationParticipant(TimeStampedModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_participations",
    )
    role = models.CharField(
        max_length=32,
        choices=ConversationParticipantRole.choices,
        default=ConversationParticipantRole.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="messaging_conversation_participant_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "left_at"]),
        ]
