from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from accounts.models.profile import ProfileVisibility


class MessageAudience(models.TextChoices):
    EVERYONE = "everyone", "Everyone"
    FOLLOWERS = "followers", "Followers"
    FRIENDS = "friends", "Friends"
    NOBODY = "nobody", "Nobody"


class UserPrivacySettings(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="privacy_settings",
    )
    profile_visibility = models.CharField(
        max_length=16,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.PUBLIC,
    )
    show_online_status = models.BooleanField(default=True)
    show_study_activity = models.BooleanField(default=True)
    show_last_active = models.BooleanField(default=True)
    allow_discovery = models.BooleanField(default=True)
    allow_messages_from = models.CharField(
        max_length=16,
        choices=MessageAudience.choices,
        default=MessageAudience.EVERYONE,
    )
    show_in_rankings = models.BooleanField(default=True)
    show_email_on_profile = models.BooleanField(default=False)
    show_phone_on_profile = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Privacy settings for {self.user_id}"


class UserBlock(TimeStampedModel):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_initiated",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_received",
    )
    reason = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "blocked"],
                name="accounts_user_block_unique",
            ),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="accounts_user_block_not_self",
            ),
        ]
        indexes = [
            models.Index(fields=["blocker", "created_at"]),
            models.Index(fields=["blocked", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.blocker_id} blocked {self.blocked_id}"


class UserMute(TimeStampedModel):
    muter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mutes_initiated",
    )
    muted = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mutes_received",
    )
    mute_posts = models.BooleanField(default=True)
    mute_notifications = models.BooleanField(default=True)
    mute_messages = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["muter", "muted"],
                name="accounts_user_mute_unique",
            ),
            models.CheckConstraint(
                condition=~models.Q(muter=models.F("muted")),
                name="accounts_user_mute_not_self",
            ),
        ]
        indexes = [
            models.Index(fields=["muter", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.muter_id} muted {self.muted_id}"
