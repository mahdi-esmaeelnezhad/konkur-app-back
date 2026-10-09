from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class VerificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    PHONE = "phone", "Phone"
    IDENTITY = "identity", "Identity"


class VerificationRecordStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    VERIFIED = "verified", "Verified"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class AccountVerification(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_verifications",
    )
    channel = models.CharField(max_length=32, choices=VerificationChannel.choices)
    target = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=VerificationRecordStatus.choices,
        default=VerificationRecordStatus.PENDING,
        db_index=True,
    )
    token_hash = models.CharField(max_length=128, blank=True, default="")
    code_hint = models.CharField(max_length=8, blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "channel", "status"]),
            models.Index(fields=["token_hash"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel} verification for {self.user_id} ({self.status})"
