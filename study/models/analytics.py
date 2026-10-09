from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class StreakType(models.TextChoices):
    DAILY_STUDY = "daily_study", "Daily study"
    GOAL = "goal", "Goal"
    QUESTIONS = "questions", "Questions"


class PersonalRecordKind(models.TextChoices):
    LONGEST_SESSION = "longest_session", "Longest session"
    MOST_QUESTIONS = "most_questions", "Most questions in a day"
    HIGHEST_SCORE = "highest_score", "Highest test score"
    LONGEST_STREAK = "longest_streak", "Longest streak"
    MOST_ACTIVE_DAY = "most_active_day", "Most active day"


class AnalyticsJobStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class DailyStudySummary(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_study_summaries",
    )
    date = models.DateField(db_index=True)
    total_active_seconds = models.PositiveIntegerField(default=0)
    session_count = models.PositiveIntegerField(default=0)
    productive_seconds = models.PositiveIntegerField(default=0)
    questions_solved = models.PositiveIntegerField(default=0)
    goals_completed = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "daily_study_summaries"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"],
                name="study_daily_summary_user_date_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(total_active_seconds__gte=0),
                name="study_daily_summary_active_non_negative",
            ),
        ]


class WeeklyStudySummary(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weekly_study_summaries",
    )
    week_start = models.DateField(db_index=True)
    total_active_seconds = models.PositiveIntegerField(default=0)
    session_count = models.PositiveIntegerField(default=0)
    average_daily_seconds = models.PositiveIntegerField(default=0)
    questions_solved = models.PositiveIntegerField(default=0)
    goals_completed = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "weekly_study_summaries"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "week_start"],
                name="study_weekly_summary_user_week_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(total_active_seconds__gte=0),
                name="study_weekly_summary_active_non_negative",
            ),
        ]


class SubjectAnalyticsSnapshot(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subject_analytics_snapshots",
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.CASCADE,
        related_name="analytics_snapshots",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    total_active_seconds = models.PositiveIntegerField(default=0)
    session_count = models.PositiveIntegerField(default=0)
    questions_solved = models.PositiveIntegerField(default=0)
    accuracy_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "subject_analytics_snapshots"
        indexes = [
            models.Index(fields=["user", "subject", "period_start"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_active_seconds__gte=0),
                name="study_subject_analytics_active_non_negative",
            ),
        ]


class StreakRecord(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="streak_records",
    )
    streak_type = models.CharField(
        max_length=24,
        choices=StreakType.choices,
        default=StreakType.DAILY_STUDY,
        db_index=True,
    )
    current_count = models.PositiveIntegerField(default=0)
    longest_count = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "streak_records"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "streak_type"],
                name="study_streak_record_user_type_unique",
            ),
        ]


class PersonalRecord(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_records",
    )
    kind = models.CharField(max_length=32, choices=PersonalRecordKind.choices)
    value = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=32, blank=True)
    achieved_at = models.DateTimeField(db_index=True)
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="personal_records",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "personal_records"
        indexes = [
            models.Index(fields=["user", "kind"]),
        ]


class StudyHeatmapCell(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_heatmap_cells",
    )
    date = models.DateField(db_index=True)
    active_seconds = models.PositiveIntegerField(default=0)
    intensity_level = models.PositiveSmallIntegerField(default=0)
    session_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "study_heatmap_cells"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"],
                name="study_heatmap_user_date_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(active_seconds__gte=0),
                name="study_heatmap_active_non_negative",
            ),
        ]


class AnalyticsJobCheckpoint(TimeStampedModel):
    job_name = models.CharField(max_length=128, db_index=True)
    period_key = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=AnalyticsJobStatus.choices,
        default=AnalyticsJobStatus.PENDING,
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "analytics_job_checkpoints"
        constraints = [
            models.UniqueConstraint(
                fields=["job_name", "period_key"],
                name="study_analytics_job_checkpoint_unique",
            ),
        ]
