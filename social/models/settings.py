from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class UserSocialSettings(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_settings",
    )
    default_post_visibility = models.CharField(
        max_length=16,
        default="public",
    )
    allow_friend_requests = models.BooleanField(default=True)
    allow_follows = models.BooleanField(default=True)
    show_activity_status = models.BooleanField(default=True)
    show_study_activity = models.BooleanField(default=True)
    discoverable_in_rankings = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Social settings for {self.user_id}"


class UserSocialReportStatus(models.TextChoices):
    OPEN = "open", "Open"
    REVIEWED = "reviewed", "Reviewed"
    DISMISSED = "dismissed", "Dismissed"


class UserSocialReport(TimeStampedModel):
    """Lightweight social-layer report; full moderation lives in safety."""

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_reports_filed",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_reports_received",
    )
    post = models.ForeignKey(
        "social.Post",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="social_reports",
    )
    reason_code = models.CharField(max_length=64, db_index=True)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=UserSocialReportStatus.choices,
        default=UserSocialReportStatus.OPEN,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["reported_user", "status", "-created_at"]),
            models.Index(fields=["reporter", "-created_at"]),
        ]
