from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ParentChildRelationshipStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"


class ParentChildRelationship(TimeStampedModel):
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_child_links_as_parent",
    )
    child = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_child_links_as_child",
    )
    status = models.CharField(
        max_length=32,
        choices=ParentChildRelationshipStatus.choices,
        default=ParentChildRelationshipStatus.PENDING,
        db_index=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    invited_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "child"],
                name="org_parent_child_unique",
            ),
            models.CheckConstraint(
                condition=~models.Q(parent=models.F("child")),
                name="org_parent_child_not_self",
            ),
        ]
        indexes = [
            models.Index(fields=["child", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.parent_id} → {self.child_id} ({self.status})"


class ParentPermissionKind(models.TextChoices):
    VIEW_PROGRESS = "view_progress", "View progress"
    VIEW_ATTENDANCE = "view_attendance", "View attendance"
    VIEW_REPORTS = "view_reports", "View reports"
    RECEIVE_ALERTS = "receive_alerts", "Receive alerts"
    MANAGE_GOALS = "manage_goals", "Manage goals"


class ParentPermission(TimeStampedModel):
    relationship = models.ForeignKey(
        ParentChildRelationship,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    permission = models.CharField(max_length=64, choices=ParentPermissionKind.choices)
    granted = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["relationship", "permission"],
                name="org_parent_permission_unique",
            ),
        ]


class ParentReportFrequency(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    NEVER = "never", "Never"


class ParentReportPreference(TimeStampedModel):
    relationship = models.OneToOneField(
        ParentChildRelationship,
        on_delete=models.CASCADE,
        related_name="report_preference",
    )
    frequency = models.CharField(
        max_length=16,
        choices=ParentReportFrequency.choices,
        default=ParentReportFrequency.WEEKLY,
    )
    include_study_summary = models.BooleanField(default=True)
    include_attendance = models.BooleanField(default=True)
    include_assignments = models.BooleanField(default=True)
    delivery_channels = models.JSONField(default=list, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
