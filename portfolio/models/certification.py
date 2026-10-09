from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Certification(TimeStampedModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class UserCertificationStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In progress"
    EARNED = "earned", "Earned"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class UserCertification(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_certifications",
    )
    certification = models.ForeignKey(
        Certification,
        on_delete=models.CASCADE,
        related_name="user_certifications",
    )
    status = models.CharField(
        max_length=32,
        choices=UserCertificationStatus.choices,
        default=UserCertificationStatus.IN_PROGRESS,
        db_index=True,
    )
    earned_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    credential_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "certification"],
                name="portfolio_user_certification_unique",
            ),
        ]


class IssuedCertificateStatus(models.TextChoices):
    ISSUED = "issued", "Issued"
    REVOKED = "revoked", "Revoked"


class IssuedCertificate(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issued_certificates",
    )
    user_certification = models.ForeignKey(
        UserCertification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_certificates",
    )
    serial_number = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    issued_at = models.DateTimeField()
    status = models.CharField(
        max_length=32,
        choices=IssuedCertificateStatus.choices,
        default=IssuedCertificateStatus.ISSUED,
        db_index=True,
    )
    document_url = models.URLField(max_length=1024, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "issued_at"]),
        ]


class CertificateVerificationResult(models.TextChoices):
    VALID = "valid", "Valid"
    INVALID = "invalid", "Invalid"
    REVOKED = "revoked", "Revoked"


class CertificateVerification(TimeStampedModel):
    certificate = models.ForeignKey(
        IssuedCertificate,
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificate_verifications",
    )
    result = models.CharField(
        max_length=16,
        choices=CertificateVerificationResult.choices,
    )
    verified_at = models.DateTimeField(auto_now_add=True)
    verification_code = models.CharField(max_length=64, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["certificate", "verified_at"]),
        ]
