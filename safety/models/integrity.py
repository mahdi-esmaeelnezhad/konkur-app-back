from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class VerificationReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class VerificationReviewKind(models.TextChoices):
    IDENTITY = "identity", "Identity"
    STUDENT = "student", "Student status"
    COACH = "coach", "Coach credentials"


class VerificationReview(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_reviews",
    )
    kind = models.CharField(max_length=32, choices=VerificationReviewKind.choices)
    status = models.CharField(
        max_length=32,
        choices=VerificationReviewStatus.choices,
        default=VerificationReviewStatus.PENDING,
        db_index=True,
    )
    submitted_payload = models.JSONField(default=dict, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_reviews_handled",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["user", "kind", "status"]),
        ]


class StudyIntegrityFlagSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class StudyIntegrityFlagStatus(models.TextChoices):
    OPEN = "open", "Open"
    CONFIRMED = "confirmed", "Confirmed"
    CLEARED = "cleared", "Cleared"


class StudyIntegrityFlag(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_integrity_flags",
    )
    study_session = models.ForeignKey(
        "study.StudySession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integrity_flags",
    )
    flag_type = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(
        max_length=16,
        choices=StudyIntegrityFlagSeverity.choices,
        default=StudyIntegrityFlagSeverity.MEDIUM,
    )
    status = models.CharField(
        max_length=32,
        choices=StudyIntegrityFlagStatus.choices,
        default=StudyIntegrityFlagStatus.OPEN,
        db_index=True,
    )
    details = models.JSONField(default=dict, blank=True)
    detected_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "detected_at"]),
        ]


class StudyVerificationEventKind(models.TextChoices):
    FLAG_CREATED = "flag_created", "Flag created"
    REVIEW_STARTED = "review_started", "Review started"
    CLEARED = "cleared", "Cleared"
    CONFIRMED = "confirmed", "Confirmed"
    APPEAL = "appeal", "Appeal"


class StudyVerificationEvent(TimeStampedModel):
    flag = models.ForeignKey(
        StudyIntegrityFlag,
        on_delete=models.CASCADE,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_verification_events",
    )
    event_kind = models.CharField(
        max_length=32,
        choices=StudyVerificationEventKind.choices,
    )
    notes = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["flag", "created_at"]),
        ]
