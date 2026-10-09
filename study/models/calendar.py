from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class CalendarEventSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    STUDY_PLAN = "study_plan", "Study plan"
    PLANNED_SESSION = "planned_session", "Planned session"
    DEADLINE = "deadline", "Deadline"
    EXTERNAL = "external", "External"


class CalendarParticipantRole(models.TextChoices):
    ORGANIZER = "organizer", "Organizer"
    ATTENDEE = "attendee", "Attendee"
    COACH = "coach", "Coach"
    OBSERVER = "observer", "Observer"


class CalendarParticipantResponse(models.TextChoices):
    NEEDS_ACTION = "needs_action", "Needs action"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    TENTATIVE = "tentative", "Tentative"


class ReminderStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    SENT = "sent", "Sent"
    DISMISSED = "dismissed", "Dismissed"
    CANCELLED = "cancelled", "Cancelled"


class ReminderChannel(models.TextChoices):
    PUSH = "push", "Push"
    EMAIL = "email", "Email"
    IN_APP = "in_app", "In app"
    SMS = "sms", "SMS"


class DeadlineStatus(models.TextChoices):
    OPEN = "open", "Open"
    MET = "met", "Met"
    MISSED = "missed", "Missed"
    CANCELLED = "cancelled", "Cancelled"


class DeadlinePriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class CalendarEvent(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    timezone = models.CharField(max_length=64, default="UTC")
    source = models.CharField(
        max_length=24,
        choices=CalendarEventSource.choices,
        default=CalendarEventSource.MANUAL,
    )
    location = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "calendar_events"
        indexes = [
            models.Index(fields=["owner", "starts_at"]),
        ]


class CalendarEventParticipant(TimeStampedModel):
    event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_event_participations",
    )
    role = models.CharField(
        max_length=16,
        choices=CalendarParticipantRole.choices,
        default=CalendarParticipantRole.ATTENDEE,
    )
    response_status = models.CharField(
        max_length=16,
        choices=CalendarParticipantResponse.choices,
        default=CalendarParticipantResponse.NEEDS_ACTION,
    )

    class Meta:
        db_table = "calendar_event_participants"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="study_calendar_event_participant_unique",
            ),
        ]


class ReminderRule(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reminder_rules",
    )
    name = models.CharField(max_length=128)
    channel = models.CharField(
        max_length=16,
        choices=ReminderChannel.choices,
        default=ReminderChannel.IN_APP,
    )
    offset_minutes = models.PositiveIntegerField(default=15)
    is_enabled = models.BooleanField(default=True)
    applies_to_goals = models.BooleanField(default=True)
    applies_to_deadlines = models.BooleanField(default=True)
    applies_to_sessions = models.BooleanField(default=True)

    class Meta:
        db_table = "reminder_rules"
        indexes = [
            models.Index(fields=["user", "is_enabled"]),
        ]


class Reminder(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    rule = models.ForeignKey(
        ReminderRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reminders",
    )
    title = models.CharField(max_length=255)
    remind_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=16,
        choices=ReminderStatus.choices,
        default=ReminderStatus.SCHEDULED,
        db_index=True,
    )
    channel = models.CharField(
        max_length=16,
        choices=ReminderChannel.choices,
        default=ReminderChannel.IN_APP,
    )
    goal = models.ForeignKey(
        "study.Goal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminders",
    )
    deadline = models.ForeignKey(
        "study.Deadline",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminders",
    )
    planned_session = models.ForeignKey(
        "study.PlannedSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminders",
    )
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reminders"
        indexes = [
            models.Index(fields=["user", "remind_at"]),
            models.Index(fields=["user", "status"]),
        ]


class Deadline(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deadlines",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=16,
        choices=DeadlineStatus.choices,
        default=DeadlineStatus.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=16,
        choices=DeadlinePriority.choices,
        default=DeadlinePriority.MEDIUM,
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deadlines",
    )
    exam = models.ForeignKey(
        "education.Exam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deadlines",
    )
    goal = models.ForeignKey(
        "study.Goal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deadlines",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "deadlines"
        indexes = [
            models.Index(fields=["user", "due_at"]),
            models.Index(fields=["user", "status", "due_at"]),
        ]
