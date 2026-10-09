from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ReferralCode(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_codes",
    )
    code = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]


class ReferralEventKind(models.TextChoices):
    SIGNUP = "signup", "Signup"
    SUBSCRIPTION = "subscription", "Subscription"
    PURCHASE = "purchase", "Purchase"


class ReferralEvent(TimeStampedModel):
    referral_code = models.ForeignKey(
        ReferralCode,
        on_delete=models.CASCADE,
        related_name="events",
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_events_as_referred",
    )
    event_kind = models.CharField(max_length=32, choices=ReferralEventKind.choices)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["referral_code", "referred_user", "event_kind"],
                name="billing_referral_event_unique",
            ),
        ]


class ReferralRewardStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    GRANTED = "granted", "Granted"
    REVOKED = "revoked", "Revoked"


class ReferralReward(TimeStampedModel):
    event = models.OneToOneField(
        ReferralEvent,
        on_delete=models.CASCADE,
        related_name="reward",
    )
    beneficiary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_rewards",
    )
    status = models.CharField(
        max_length=32,
        choices=ReferralRewardStatus.choices,
        default=ReferralRewardStatus.PENDING,
        db_index=True,
    )
    amount_minor = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="IRR")
    reward_type = models.CharField(max_length=64, default="credit")
    granted_at = models.DateTimeField(null=True, blank=True)
