from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models.organization import Organization
from org.models.school import School


class AnnouncementAudience(models.TextChoices):
    ORGANIZATION = "organization", "Organization"
    SCHOOL = "school", "School"
    CLASS = "class", "Class"


class Announcement(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcements",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcements",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements_authored",
    )
    audience = models.CharField(max_length=32, choices=AnnouncementAudience.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["school", "published_at"]),
            models.Index(fields=["organization", "published_at"]),
        ]
