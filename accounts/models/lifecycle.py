from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class AccountDeletionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SCHEDULED = "scheduled", "Scheduled"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class AccountDeletionRequest(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deletion_requests",
    )
    status = models.CharField(
        max_length=32,
        choices=AccountDeletionStatus.choices,
        default=AccountDeletionStatus.PENDING,
        db_index=True,
    )
    reason_code = models.CharField(max_length=64, blank=True, default="")
    feedback = models.TextField(blank=True, default="")
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    anonymize_only = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
            models.Index(fields=["status", "scheduled_for"]),
        ]

    def __str__(self) -> str:
        return f"Deletion request for {self.user_id} ({self.status})"
