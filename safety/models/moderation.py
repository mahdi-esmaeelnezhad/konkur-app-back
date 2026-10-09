from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from safety.models.report import Report


class ModerationCaseStatus(models.TextChoices):
    OPEN = "open", "Open"
    ESCALATED = "escalated", "Escalated"
    CLOSED = "closed", "Closed"


class ModerationCasePriority(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    URGENT = "urgent", "Urgent"


class ModerationCase(TimeStampedModel):
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_cases",
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_cases_as_subject",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_cases_assigned",
    )
    status = models.CharField(
        max_length=32,
        choices=ModerationCaseStatus.choices,
        default=ModerationCaseStatus.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=16,
        choices=ModerationCasePriority.choices,
        default=ModerationCasePriority.NORMAL,
    )
    summary = models.TextField(blank=True, default="")
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "priority", "created_at"]),
        ]


class ModerationActionKind(models.TextChoices):
    WARN = "warn", "Warn"
    REMOVE_CONTENT = "remove_content", "Remove content"
    SUSPEND = "suspend", "Suspend"
    BAN = "ban", "Ban"
    NOTE = "note", "Note"
    DISMISS = "dismiss", "Dismiss"


class ModerationAction(TimeStampedModel):
    case = models.ForeignKey(
        ModerationCase,
        on_delete=models.CASCADE,
        related_name="actions",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_actions_taken",
    )
    action = models.CharField(max_length=32, choices=ModerationActionKind.choices)
    notes = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "created_at"]),
        ]
