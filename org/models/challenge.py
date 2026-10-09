from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models.organization import Organization
from org.models.school import School


class InstitutionalChallengeStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class InstitutionalChallenge(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="challenges",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="challenges",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="institutional_challenges_created",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=InstitutionalChallengeStatus.choices,
        default=InstitutionalChallengeStatus.DRAFT,
        db_index=True,
    )
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    target_metric = models.CharField(max_length=64, blank=True, default="study_minutes")
    target_value = models.PositiveIntegerField(null=True, blank=True)
    rules = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status", "starts_at"]),
        ]
