from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ProfileVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    FRIENDS = "friends", "Friends only"
    PRIVATE = "private", "Private"


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=255, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    avatar_url = models.URLField(max_length=512, blank=True, default="")
    cover_url = models.URLField(max_length=512, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)
    country_code = models.CharField(max_length=2, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    website_url = models.URLField(max_length=512, blank=True, default="")
    public_slug = models.SlugField(max_length=64, blank=True, default="")
    is_identity_verified = models.BooleanField(default=False)
    default_visibility = models.CharField(
        max_length=16,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.PUBLIC,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["public_slug"],
                condition=~models.Q(public_slug=""),
                name="accounts_user_profile_public_slug_unique_nonempty",
            ),
        ]

    def __str__(self) -> str:
        return f"Profile for {self.user_id}"
