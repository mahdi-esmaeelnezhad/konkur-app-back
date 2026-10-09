from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from coaching.models.profile import CoachProfile


class CoachStudentRelationshipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ENDED = "ended", "Ended"


class CoachStudentRelationship(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="student_relationships",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_relationships",
    )
    status = models.CharField(
        max_length=16,
        choices=CoachStudentRelationshipStatus.choices,
        default=CoachStudentRelationshipStatus.ACTIVE,
        db_index=True,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["coach", "student"],
                condition=models.Q(status=CoachStudentRelationshipStatus.ACTIVE),
                name="coaching_active_relationship_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["coach", "status"]),
        ]


class CoachStudentRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    WITHDRAWN = "withdrawn", "Withdrawn"


class CoachStudentRequest(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="student_requests",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_requests",
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=CoachStudentRequestStatus.choices,
        default=CoachStudentRequestStatus.PENDING,
        db_index=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["coach", "student"],
                condition=models.Q(status=CoachStudentRequestStatus.PENDING),
                name="coaching_student_request_unique_pending",
            ),
        ]
        indexes = [
            models.Index(fields=["coach", "status", "-created_at"]),
        ]


class CoachReferral(TimeStampedModel):
    referrer_coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="referrals_sent",
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coach_referrals_received",
    )
    referral_code = models.CharField(max_length=64, unique=True, db_index=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["referrer_coach", "-created_at"]),
        ]


class CoachAvailability(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    day_of_week = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=64, default="UTC")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(day_of_week__gte=0, day_of_week__lte=6),
                name="coaching_availability_valid_dow",
            ),
            models.CheckConstraint(
                condition=models.Q(start_time__lt=models.F("end_time")),
                name="coaching_availability_valid_range",
            ),
        ]
        indexes = [
            models.Index(fields=["coach", "day_of_week"]),
        ]
