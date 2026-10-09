from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models import Organization


class PaymentCustomerOwnerKind(models.TextChoices):
    USER = "user", "User"
    ORGANIZATION = "organization", "Organization"


class PaymentCustomer(TimeStampedModel):
    owner_kind = models.CharField(max_length=32, choices=PaymentCustomerOwnerKind.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payment_customers",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payment_customers",
    )
    external_customer_id = models.CharField(max_length=255, unique=True)
    default_currency = models.CharField(max_length=3, default="IRR")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(owner_kind="user", user__isnull=False, organization__isnull=True)
                    | models.Q(
                        owner_kind="organization",
                        organization__isnull=False,
                        user__isnull=True,
                    )
                ),
                name="billing_payment_customer_owner_consistency",
            ),
        ]


class PaymentTransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class PaymentTransactionKind(models.TextChoices):
    CHARGE = "charge", "Charge"
    SUBSCRIPTION = "subscription", "Subscription"
    MARKETPLACE = "marketplace", "Marketplace"
    PAYOUT = "payout", "Payout"
    ADJUSTMENT = "adjustment", "Adjustment"


class PaymentTransaction(TimeStampedModel):
    customer = models.ForeignKey(
        PaymentCustomer,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
    )
    kind = models.CharField(max_length=32, choices=PaymentTransactionKind.choices)
    status = models.CharField(
        max_length=32,
        choices=PaymentTransactionStatus.choices,
        default=PaymentTransactionStatus.PENDING,
        db_index=True,
    )
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    idempotency_key = models.CharField(max_length=128, unique=True)
    external_payment_id = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=512, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_minor__gt=0),
                name="billing_payment_tx_amount_positive",
            ),
            models.UniqueConstraint(
                fields=["external_payment_id"],
                condition=~models.Q(external_payment_id=""),
                name="billing_payment_tx_external_id_unique",
            ),
        ]


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    OPEN = "open", "Open"
    PAID = "paid", "Paid"
    VOID = "void", "Void"
    UNCOLLECTIBLE = "uncollectible", "Uncollectible"


class Invoice(TimeStampedModel):
    customer = models.ForeignKey(
        PaymentCustomer,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=32,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True,
    )
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    line_items = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "status"]),
        ]


class RefundStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class Refund(TimeStampedModel):
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.PROTECT,
        related_name="refunds",
    )
    status = models.CharField(
        max_length=32,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
        db_index=True,
    )
    amount_minor = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    reason = models.TextField(blank=True, default="")
    external_refund_id = models.CharField(max_length=255, blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["transaction", "status"]),
        ]


class PaymentWebhookProcessingStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"
    IGNORED = "ignored", "Ignored"


class PaymentWebhookEvent(TimeStampedModel):
    provider = models.CharField(max_length=64, db_index=True)
    external_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=128, db_index=True)
    payload = models.JSONField(default=dict)
    processing_status = models.CharField(
        max_length=32,
        choices=PaymentWebhookProcessingStatus.choices,
        default=PaymentWebhookProcessingStatus.RECEIVED,
        db_index=True,
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["provider", "processing_status", "created_at"]),
        ]
