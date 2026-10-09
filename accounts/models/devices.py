from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class UserDevicePlatform(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"
    WEB = "web", "Web"
    DESKTOP = "desktop", "Desktop"


class UserDevice(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    platform = models.CharField(max_length=16, choices=UserDevicePlatform.choices)
    device_fingerprint = models.CharField(max_length=128)
    device_label = models.CharField(max_length=128, blank=True, default="")
    app_version = models.CharField(max_length=64, blank=True, default="")
    os_version = models.CharField(max_length=64, blank=True, default="")
    push_token = models.CharField(max_length=512, blank=True, default="")
    is_trusted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "platform", "device_fingerprint"],
                name="accounts_user_device_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "is_active", "last_seen_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.platform} device for {self.user_id}"
