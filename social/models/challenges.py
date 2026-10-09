from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ChallengeMetric(models.TextChoices):
    STUDY_MINUTES = "study_minutes", "Study minutes"
    STREAK_DAYS = "streak_days", "Streak days"
    QUESTIONS = "questions", "Questions answered"
    SESSIONS = "sessions", "Study sessions"


class ChallengeStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Challenge(TimeStampedModel):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenges_created",
    )
    community = models.ForeignKey(
        "social.Community",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="challenges",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    metric = models.CharField(max_length=32, choices=ChallengeMetric.choices, db_index=True)
    target_value = models.PositiveIntegerField()
    unit = models.CharField(max_length=32)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=16,
        choices=ChallengeStatus.choices,
        default=ChallengeStatus.DRAFT,
        db_index=True,
    )
    xp_reward = models.PositiveIntegerField(default=0)
    badge_name = models.CharField(max_length=128, blank=True)
    participant_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["status", "starts_at"]),
            models.Index(fields=["community", "status"]),
        ]


class ChallengeParticipantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    WITHDRAWN = "withdrawn", "Withdrawn"


class ChallengeParticipant(TimeStampedModel):
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenge_participations",
    )
    status = models.CharField(
        max_length=16,
        choices=ChallengeParticipantStatus.choices,
        default=ChallengeParticipantStatus.ACTIVE,
        db_index=True,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["challenge", "user"],
                name="social_challenge_participant_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]


class ChallengeGoal(TimeStampedModel):
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="goals",
    )
    title = models.CharField(max_length=255)
    target_value = models.PositiveIntegerField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]


class ChallengeProgress(TimeStampedModel):
    participant = models.ForeignKey(
        ChallengeParticipant,
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    goal = models.ForeignKey(
        ChallengeGoal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="progress_entries",
    )
    current_value = models.PositiveIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "goal"],
                condition=models.Q(goal__isnull=False),
                name="social_challenge_progress_unique_goal",
            ),
        ]
        indexes = [
            models.Index(fields=["participant", "-recorded_at"]),
        ]
