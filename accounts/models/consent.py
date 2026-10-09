from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ConsentType(models.TextChoices):
    TERMS_OF_SERVICE = "terms_of_service", "Terms of service"
    PRIVACY_POLICY = "privacy_policy", "Privacy policy"
    MARKETING = "marketing", "Marketing"
    ANALYTICS = "analytics", "Analytics"
    PARENTAL = "parental", "Parental consent"
    COOKIES = "cookies", "Cookies"


class UserConsent(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consents",
    )
    consent_type = models.CharField(max_length=64, choices=ConsentType.choices)
    version = models.CharField(max_length=32)
    accepted = models.BooleanField(default=True)
    accepted_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "consent_type", "version"],
                name="accounts_user_consent_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "consent_type", "-accepted_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.consent_type} v{self.version} for {self.user_id}"
