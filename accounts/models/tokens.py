from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class RefreshToken(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    device = models.ForeignKey(
        "accounts.UserDevice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refresh_tokens",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    replaced_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replacements",
    )

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["user", "revoked_at"]),
        ]

    def __str__(self) -> str:
        return f"Refresh token for {self.user_id}"
