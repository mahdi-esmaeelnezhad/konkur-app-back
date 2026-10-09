from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class GoalStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    PAUSED = "paused", "Paused"
    CANCELLED = "cancelled", "Cancelled"


class GoalVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    FRIENDS = "friends", "Friends"
    COACH = "coach", "Coach"
    PUBLIC = "public", "Public"


class GoalType(TimeStampedModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    default_unit = models.CharField(max_length=32, blank=True)
    is_system = models.BooleanField(default=True)

    class Meta:
        db_table = "goal_types"

    def __str__(self) -> str:
        return self.name


class Goal(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goals",
    )
    goal_type = models.ForeignKey(
        GoalType,
        on_delete=models.PROTECT,
        related_name="goals",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_value = models.DecimalField(max_digits=14, decimal_places=4)
    current_value = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    unit = models.CharField(max_length=32)
    status = models.CharField(
        max_length=16,
        choices=GoalStatus.choices,
        default=GoalStatus.ACTIVE,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=16,
        choices=GoalVisibility.choices,
        default=GoalVisibility.PRIVATE,
    )
    deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )
    exam = models.ForeignKey(
        "education.Exam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_goals",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "goals"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "deadline"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_value__gt=0),
                name="study_goal_target_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(current_value__gte=0),
                name="study_goal_current_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class GoalProgressSnapshot(TimeStampedModel):
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name="progress_snapshots",
    )
    captured_at = models.DateTimeField(db_index=True)
    current_value = models.DecimalField(max_digits=14, decimal_places=4)
    progress_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "goal_progress_snapshots"
        indexes = [
            models.Index(fields=["goal", "-captured_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(current_value__gte=0),
                name="study_goal_snapshot_current_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(progress_percent__gte=0)
                & models.Q(progress_percent__lte=100),
                name="study_goal_snapshot_percent_range",
            ),
        ]
