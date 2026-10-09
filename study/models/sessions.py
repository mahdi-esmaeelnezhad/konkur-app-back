from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class StudySessionStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class StudySessionSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    TIMER = "timer", "Timer"


class StudySessionVerificationStatus(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not required"
    PENDING = "pending", "Pending"
    VERIFIED = "verified", "Verified"
    REJECTED = "rejected", "Rejected"
    SUSPICIOUS = "suspicious", "Suspicious"
    UNVERIFIED = "unverified", "Unverified"


class StudyActivityType(models.TextChoices):
    STUDY = "study", "Study"
    TEST_PRACTICE = "test_practice", "Test practice"
    REVIEW = "review", "Review"
    FLASHCARD = "flashcard", "Flashcard"
    LECTURE = "lecture", "Lecture"
    PROJECT = "project", "Project"
    BREAK = "break", "Break"


class StudySessionEventType(models.TextChoices):
    START = "start", "Start"
    PAUSE = "pause", "Pause"
    RESUME = "resume", "Resume"
    BREAK_START = "break_start", "Break start"
    BREAK_END = "break_end", "Break end"
    COMPLETE = "complete", "Complete"
    CANCEL = "cancel", "Cancel"
    NOTE_ADDED = "note_added", "Note added"
    SUBJECT_SWITCH = "subject_switch", "Subject switch"


class StudySessionVerificationReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    NEEDS_REVIEW = "needs_review", "Needs review"


class StudySession(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_sessions",
    )
    status = models.CharField(
        max_length=16,
        choices=StudySessionStatus.choices,
        default=StudySessionStatus.PLANNED,
        db_index=True,
    )
    source = models.CharField(
        max_length=16,
        choices=StudySessionSource.choices,
        default=StudySessionSource.TIMER,
    )
    verification_status = models.CharField(
        max_length=16,
        choices=StudySessionVerificationStatus.choices,
        default=StudySessionVerificationStatus.NOT_REQUIRED,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    paused_seconds = models.PositiveIntegerField(default=0)
    timezone = models.CharField(max_length=64, default="UTC")
    activity_type = models.CharField(
        max_length=24,
        choices=StudyActivityType.choices,
        default=StudyActivityType.STUDY,
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    goal = models.ForeignKey(
        "study.Goal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    planned_session = models.ForeignKey(
        "study.PlannedSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    plan_item = models.ForeignKey(
        "study.StudyPlanItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    exam = models.ForeignKey(
        "education.Exam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    notes_summary = models.TextField(blank=True)
    questions_solved = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    is_pomodoro = models.BooleanField(default=False)
    client_reported_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "study_sessions"
        indexes = [
            models.Index(fields=["user", "started_at"]),
            models.Index(fields=["user", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(active_seconds__gte=0),
                name="study_session_active_seconds_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(paused_seconds__gte=0),
                name="study_session_paused_seconds_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(ended_at__isnull=True)
                | models.Q(started_at__isnull=True)
                | models.Q(ended_at__gte=models.F("started_at")),
                name="study_session_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(correct_answers__lte=models.F("questions_solved"))
                & models.Q(wrong_answers__lte=models.F("questions_solved")),
                name="study_session_answer_counts_lte_questions",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(
                    status__in=["active", "paused"],
                    deleted_at__isnull=True,
                ),
                name="study_session_one_live_per_user",
            ),
        ]

    def __str__(self) -> str:
        return self.title or f"Session {self.pk}"


class StudySessionEvent(TimeStampedModel):
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(
        max_length=24,
        choices=StudySessionEventType.choices,
        db_index=True,
    )
    occurred_at = models.DateTimeField(db_index=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "study_session_events"
        indexes = [
            models.Index(fields=["session", "occurred_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="study_session_event_unique_idempotency",
            ),
        ]


class StudySessionNote(TimeStampedModel):
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_session_notes",
    )
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)

    class Meta:
        db_table = "study_session_notes"
        indexes = [
            models.Index(fields=["session", "-created_at"]),
        ]


class StudyBreak(TimeStampedModel):
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="breaks",
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "study_breaks"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_break_duration_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(ended_at__isnull=True)
                | models.Q(ended_at__gte=models.F("started_at")),
                name="study_break_end_after_start",
            ),
        ]


class StudyActivity(TimeStampedModel):
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    activity_type = models.CharField(
        max_length=24,
        choices=StudyActivityType.choices,
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "study_activities"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_activity_duration_non_negative",
            ),
        ]


class StudySessionSubject(TimeStampedModel):
    session = models.ForeignKey(
        StudySession,
        on_delete=models.CASCADE,
        related_name="session_subjects",
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.CASCADE,
        related_name="study_session_subjects",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_session_subjects",
    )
    allocation_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "study_session_subjects"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "subject"],
                name="study_session_subject_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(allocation_seconds__gte=0),
                name="study_session_subject_allocation_non_negative",
            ),
        ]


class ManualActivityLog(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manual_activity_logs",
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_activity_logs",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_activity_logs",
    )
    activity_type = models.CharField(
        max_length=24,
        choices=StudyActivityType.choices,
        default=StudyActivityType.STUDY,
    )
    logged_at = models.DateTimeField(db_index=True)
    duration_seconds = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    study_session = models.ForeignKey(
        StudySession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_logs",
    )

    class Meta:
        db_table = "manual_activity_logs"
        indexes = [
            models.Index(fields=["user", "logged_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_manual_log_duration_non_negative",
            ),
        ]


class FocusSettings(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="focus_settings",
    )
    block_distractions = models.BooleanField(default=False)
    daily_limit_seconds = models.PositiveIntegerField(null=True, blank=True)
    session_limit_seconds = models.PositiveIntegerField(null=True, blank=True)
    auto_pause_on_idle = models.BooleanField(default=True)
    idle_threshold_seconds = models.PositiveIntegerField(default=300)

    class Meta:
        db_table = "focus_settings"


class PomodoroSettings(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pomodoro_settings",
    )
    work_seconds = models.PositiveIntegerField(default=1500)
    short_break_seconds = models.PositiveIntegerField(default=300)
    long_break_seconds = models.PositiveIntegerField(default=900)
    cycles_before_long_break = models.PositiveSmallIntegerField(default=4)
    auto_start_breaks = models.BooleanField(default=False)
    auto_start_work = models.BooleanField(default=False)

    class Meta:
        db_table = "pomodoro_settings"


class StudySessionVerification(TimeStampedModel):
    session = models.OneToOneField(
        StudySession,
        on_delete=models.CASCADE,
        related_name="verification",
    )
    status = models.CharField(
        max_length=16,
        choices=StudySessionVerificationReviewStatus.choices,
        default=StudySessionVerificationReviewStatus.PENDING,
        db_index=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_session_verifications_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    flagged_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "study_session_verifications"
