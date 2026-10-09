from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ReportTargetKind(models.TextChoices):
    USER = "user", "User"
    MESSAGE = "message", "Message"
    POST = "post", "Post"
    STUDY_SESSION = "study_session", "Study session"
    OTHER = "other", "Other"


class ReportStatus(models.TextChoices):
    OPEN = "open", "Open"
    UNDER_REVIEW = "under_review", "Under review"
    RESOLVED = "resolved", "Resolved"
    DISMISSED = "dismissed", "Dismissed"


class ReportReason(models.TextChoices):
    HARASSMENT = "harassment", "Harassment"
    SPAM = "spam", "Spam"
    CHEATING = "cheating", "Cheating"
    INAPPROPRIATE = "inappropriate", "Inappropriate content"
    OTHER = "other", "Other"


class Report(TimeStampedModel):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_filed",
    )
    target_kind = models.CharField(max_length=32, choices=ReportTargetKind.choices)
    target_id = models.UUIDField(db_index=True)
    reason = models.CharField(max_length=32, choices=ReportReason.choices)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=ReportStatus.choices,
        default=ReportStatus.OPEN,
        db_index=True,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["target_kind", "target_id"]),
            models.Index(fields=["status", "created_at"]),
        ]
