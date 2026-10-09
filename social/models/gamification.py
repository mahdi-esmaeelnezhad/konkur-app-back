from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class XpSourceType(models.TextChoices):
    STUDY_SESSION = "study_session", "Study session"
    CHALLENGE = "challenge", "Challenge"
    ACHIEVEMENT = "achievement", "Achievement"
    COMMUNITY = "community", "Community"
    MANUAL = "manual", "Manual adjustment"
    REFERRAL = "referral", "Referral"


class XpTransaction(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="xp_transactions",
    )
    amount = models.IntegerField()
    source_type = models.CharField(max_length=32, choices=XpSourceType.choices, db_index=True)
    source_id = models.UUIDField(null=True, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="social_xp_transaction_unique_user_idempotency",
            ),
            models.UniqueConstraint(
                fields=["user", "source_type", "source_id"],
                condition=models.Q(source_id__isnull=False),
                name="social_xp_transaction_unique_source",
            ),
            models.CheckConstraint(
                condition=~models.Q(amount=0),
                name="social_xp_transaction_amount_nonzero",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["source_type", "source_id"]),
        ]


class LevelDefinition(TimeStampedModel):
    level = models.PositiveIntegerField(unique=True)
    xp_required = models.PositiveIntegerField()
    title = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["level"]


class UserLevel(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_level",
    )
    current_level = models.ForeignKey(
        LevelDefinition,
        on_delete=models.PROTECT,
        related_name="users_at_level",
    )
    current_xp = models.PositiveIntegerField(default=0)
    lifetime_xp = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["-current_xp"]),
        ]


class Achievement(TimeStampedModel):
    slug = models.SlugField(max_length=128, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon_url = models.URLField(max_length=2048, blank=True)
    xp_reward = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self) -> str:
        return self.title


class AchievementConditionKind(models.TextChoices):
    STUDY_MINUTES = "study_minutes", "Study minutes total"
    STREAK_DAYS = "streak_days", "Streak days"
    CHALLENGES_WON = "challenges_won", "Challenges won"
    POSTS_CREATED = "posts_created", "Posts created"
    CUSTOM = "custom", "Custom"


class AchievementCondition(TimeStampedModel):
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="conditions",
    )
    kind = models.CharField(max_length=32, choices=AchievementConditionKind.choices)
    threshold = models.PositiveIntegerField()
    parameters = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["achievement", "kind"]),
        ]


class UserAchievement(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements_earned",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="user_earnings",
    )
    earned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "achievement"],
                name="social_user_achievement_unique",
            ),
        ]


class CommunityAchievement(TimeStampedModel):
    community = models.ForeignKey(
        "social.Community",
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="community_links",
    )
    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["community", "achievement"],
                name="social_community_achievement_unique",
            ),
        ]


class RewardClaimStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CLAIMED = "claimed", "Claimed"
    EXPIRED = "expired", "Expired"


class RewardClaim(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reward_claims",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reward_claims",
    )
    xp_transaction = models.ForeignKey(
        XpTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reward_claims",
    )
    status = models.CharField(
        max_length=16,
        choices=RewardClaimStatus.choices,
        default=RewardClaimStatus.PENDING,
        db_index=True,
    )
    claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
        ]
