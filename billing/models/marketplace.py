from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class MarketplaceOrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FULFILLED = "fulfilled", "Fulfilled"
    REFUNDED = "refunded", "Refunded"
    CANCELLED = "cancelled", "Cancelled"


class MarketplaceOrder(TimeStampedModel):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marketplace_orders_as_buyer",
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marketplace_orders_as_coach",
    )
    status = models.CharField(
        max_length=32,
        choices=MarketplaceOrderStatus.choices,
        default=MarketplaceOrderStatus.PENDING,
        db_index=True,
    )
    product_code = models.CharField(max_length=64, db_index=True)
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    payment_transaction = models.ForeignKey(
        "billing.PaymentTransaction",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="marketplace_orders",
    )
    metadata = models.JSONField(default=dict, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "status", "created_at"]),
            models.Index(fields=["buyer", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_minor__gt=0),
                name="billing_marketplace_order_amount_positive",
            ),
        ]


class MarketplaceCommission(TimeStampedModel):
    order = models.OneToOneField(
        MarketplaceOrder,
        on_delete=models.CASCADE,
        related_name="commission",
    )
    platform_fee_minor = models.BigIntegerField()
    coach_earnings_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    fee_rate_bps = models.PositiveIntegerField(default=0)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(platform_fee_minor__gte=0)
                & models.Q(coach_earnings_minor__gte=0),
                name="billing_marketplace_commission_amounts_non_negative",
            ),
        ]
