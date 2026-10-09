from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from coaching.models.profile import CoachProfile


class CoachPackage(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="packages",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_minor = models.PositiveIntegerField()
    currency_code = models.CharField(max_length=3, default="IRR")
    billing_interval = models.CharField(max_length=16, default="month")
    is_active = models.BooleanField(default=True, db_index=True)
    max_students = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "is_active"]),
        ]


class CoachPackageFeature(TimeStampedModel):
    package = models.ForeignKey(
        CoachPackage,
        on_delete=models.CASCADE,
        related_name="features",
    )
    label = models.CharField(max_length=255)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]


class CoachSubscriptionStatus(models.TextChoices):
    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class CoachSubscription(TimeStampedModel):
    package = models.ForeignKey(
        CoachPackage,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_subscriptions",
    )
    status = models.CharField(
        max_length=16,
        choices=CoachSubscriptionStatus.choices,
        default=CoachSubscriptionStatus.ACTIVE,
        db_index=True,
    )
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField(db_index=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["package", "status"]),
        ]


class CoachStudentSegment(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="student_segments",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["coach", "name"],
                name="coaching_segment_unique_name",
            ),
        ]


class CoachSegmentMember(TimeStampedModel):
    segment = models.ForeignKey(
        CoachStudentSegment,
        on_delete=models.CASCADE,
        related_name="members",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_segment_memberships",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["segment", "student"],
                name="coaching_segment_member_unique",
            ),
        ]
