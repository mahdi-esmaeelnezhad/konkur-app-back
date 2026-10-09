from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models.organization import Organization
from org.models.parent import ParentChildRelationship
from org.models.school import School


class InstitutionalReportKind(models.TextChoices):
    PROGRESS = "progress", "Progress"
    ATTENDANCE = "attendance", "Attendance"
    ASSIGNMENTS = "assignments", "Assignments"
    CUSTOM = "custom", "Custom"


class InstitutionalReportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class InstitutionalReport(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    parent_relationship = models.ForeignKey(
        ParentChildRelationship,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="institutional_reports",
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="institutional_reports_about",
    )
    generated_for = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institutional_reports_received",
    )
    kind = models.CharField(max_length=32, choices=InstitutionalReportKind.choices)
    status = models.CharField(
        max_length=32,
        choices=InstitutionalReportStatus.choices,
        default=InstitutionalReportStatus.PENDING,
        db_index=True,
    )
    period_start = models.DateField()
    period_end = models.DateField()
    payload = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["subject_user", "period_start", "period_end"]),
            models.Index(fields=["status", "kind"]),
        ]
