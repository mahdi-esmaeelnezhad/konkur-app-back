from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class CoachWallet(TimeStampedModel):
    coach = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="coach_wallet",
    )
    balance_minor = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="IRR")
    is_frozen = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance_minor__gte=0),
                name="billing_coach_wallet_balance_non_negative",
            ),
        ]


class WalletTransactionKind(models.TextChoices):
    CREDIT = "credit", "Credit"
    DEBIT = "debit", "Debit"
    HOLD = "hold", "Hold"
    RELEASE = "release", "Release"


class WalletTransaction(TimeStampedModel):
    wallet = models.ForeignKey(
        CoachWallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    kind = models.CharField(max_length=16, choices=WalletTransactionKind.choices)
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    balance_after_minor = models.BigIntegerField()
    reference_type = models.CharField(max_length=64, blank=True, default="")
    reference_id = models.UUIDField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=512, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["wallet", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_minor__gt=0),
                name="billing_wallet_tx_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="billing_wallet_tx_unique_idempotency",
            ),
            models.UniqueConstraint(
                fields=["wallet", "kind", "reference_type", "reference_id"],
                condition=models.Q(reference_id__isnull=False),
                name="billing_wallet_tx_unique_reference",
            ),
        ]


class CoachPayoutStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    PROCESSING = "processing", "Processing"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class CoachPayout(TimeStampedModel):
    wallet = models.ForeignKey(
        CoachWallet,
        on_delete=models.PROTECT,
        related_name="payouts",
    )
    status = models.CharField(
        max_length=32,
        choices=CoachPayoutStatus.choices,
        default=CoachPayoutStatus.REQUESTED,
        db_index=True,
    )
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    destination = models.JSONField(default=dict, blank=True)
    external_payout_id = models.CharField(max_length=255, blank=True, default="")
    requested_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["wallet", "status"]),
        ]
