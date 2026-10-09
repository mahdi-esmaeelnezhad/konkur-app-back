import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class AccountStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    DEACTIVATED = "deactivated", "Deactivated"


class AccountVerificationStatus(models.TextChoices):
    UNVERIFIED = "unverified", "Unverified"
    PARTIAL = "partial", "Partially verified"
    VERIFIED = "verified", "Verified"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_status = models.CharField(
        max_length=32,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
        db_index=True,
    )
    verification_status = models.CharField(
        max_length=32,
        choices=AccountVerificationStatus.choices,
        default=AccountVerificationStatus.UNVERIFIED,
        db_index=True,
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    locale = models.CharField(max_length=16, default="fa", db_index=True)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=~models.Q(email=""),
                name="accounts_user_email_unique_nonempty",
            ),
            models.UniqueConstraint(
                fields=["phone"],
                condition=~models.Q(phone=""),
                name="accounts_user_phone_unique_nonempty",
            ),
        ]
        indexes = [
            models.Index(fields=["account_status", "date_joined"]),
        ]

    def __str__(self) -> str:
        return self.username
