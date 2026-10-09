from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class StudyPlanStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class StudyPlanPeriod(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    CUSTOM = "custom", "Custom"


class StudyPlanItemPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class StudyPlanAssignmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    DECLINED = "declined", "Declined"


class PlannedSessionStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    SKIPPED = "skipped", "Skipped"
    CANCELLED = "cancelled", "Cancelled"


class StudyPlan(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_plans",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=StudyPlanStatus.choices,
        default=StudyPlanStatus.DRAFT,
        db_index=True,
    )
    period = models.CharField(
        max_length=16,
        choices=StudyPlanPeriod.choices,
        default=StudyPlanPeriod.WEEKLY,
    )
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_study_plans",
    )

    class Meta:
        db_table = "study_plans"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "period_start"]),
        ]


class StudyPlanItem(TimeStampedModel):
    plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name="items",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_plan_items",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_plan_items",
    )
    scheduled_date = models.DateField(db_index=True)
    scheduled_start = models.TimeField(null=True, blank=True)
    planned_duration_seconds = models.PositiveIntegerField(default=0)
    priority = models.CharField(
        max_length=16,
        choices=StudyPlanItemPriority.choices,
        default=StudyPlanItemPriority.MEDIUM,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "study_plan_items"
        ordering = ["scheduled_date", "sort_order"]
        indexes = [
            models.Index(fields=["plan", "scheduled_date"]),
        ]


class StudyPlanAssignment(TimeStampedModel):
    plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    plan_item = models.ForeignKey(
        StudyPlanItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assignments",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_plan_assignments_received",
    )
    assigner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_plan_assignments_given",
    )
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=StudyPlanAssignmentStatus.choices,
        default=StudyPlanAssignmentStatus.PENDING,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "study_plan_assignments"
        indexes = [
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["assignee", "due_at"]),
        ]


class RecurringSchedule(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_schedules",
    )
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_schedules",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_schedules",
    )
    timezone = models.CharField(max_length=64, default="UTC")
    recurrence_rule = models.JSONField(default=dict, blank=True)
    planned_duration_seconds = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "recurring_schedules"
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]


class PlannedSession(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="planned_sessions",
    )
    plan_item = models.ForeignKey(
        StudyPlanItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_sessions",
    )
    recurring_schedule = models.ForeignKey(
        RecurringSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_sessions",
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_sessions",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    planned_duration_seconds = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=PlannedSessionStatus.choices,
        default=PlannedSessionStatus.SCHEDULED,
        db_index=True,
    )

    class Meta:
        db_table = "planned_sessions"
        indexes = [
            models.Index(fields=["user", "scheduled_start"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(planned_duration_seconds__gte=0),
                name="study_planned_session_duration_non_negative",
            ),
        ]
