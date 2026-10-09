from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from safety.models.moderation import ModerationCase


class UserSanctionKind(models.TextChoices):
    WARNING = "warning", "Warning"
    MUTE = "mute", "Mute"
    SUSPENSION = "suspension", "Suspension"
    BAN = "ban", "Ban"


class UserSanctionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class UserSanction(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sanctions",
    )
    case = models.ForeignKey(
        ModerationCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sanctions",
    )
    kind = models.CharField(max_length=32, choices=UserSanctionKind.choices)
    status = models.CharField(
        max_length=32,
        choices=UserSanctionStatus.choices,
        default=UserSanctionStatus.ACTIVE,
        db_index=True,
    )
    reason = models.TextField(blank=True, default="")
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "expires_at"]),
        ]


# BlockedUser removed: use accounts.UserBlock as the single source of truth.
