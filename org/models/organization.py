from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class OrganizationKind(models.TextChoices):
    DISTRICT = "district", "District"
    NETWORK = "network", "Network"
    NGO = "ngo", "NGO"
    OTHER = "other", "Other"


class OrganizationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class Organization(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64, unique=True)
    kind = models.CharField(
        max_length=32,
        choices=OrganizationKind.choices,
        default=OrganizationKind.OTHER,
    )
    status = models.CharField(
        max_length=32,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
        db_index=True,
    )
    country_code = models.CharField(max_length=2, blank=True, default="")
    timezone = models.CharField(max_length=64, default="UTC")
    contact_email = models.EmailField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["status", "kind"]),
        ]

    def __str__(self) -> str:
        return self.name


class OrganizationMembershipRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    STAFF = "staff", "Staff"
    VIEWER = "viewer", "Viewer"


class OrganizationMembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INVITED = "invited", "Invited"
    SUSPENDED = "suspended", "Suspended"
    LEFT = "left", "Left"


class OrganizationMembership(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=OrganizationMembershipRole.choices,
        default=OrganizationMembershipRole.STAFF,
    )
    status = models.CharField(
        max_length=16,
        choices=OrganizationMembershipStatus.choices,
        default=OrganizationMembershipStatus.ACTIVE,
        db_index=True,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_invitations_sent",
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                condition=models.Q(status=OrganizationMembershipStatus.ACTIVE),
                name="org_membership_unique_active",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["organization", "status"]),
        ]


class OrganizationDepartment(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                condition=~models.Q(code=""),
                name="org_department_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "name"]),
        ]

    def __str__(self) -> str:
        return self.name


class OrganizationSettings(TimeStampedModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    default_locale = models.CharField(max_length=16, default="fa")
    default_currency = models.CharField(max_length=3, default="IRR")
    branding = models.JSONField(default=dict, blank=True)
    feature_overrides = models.JSONField(default=dict, blank=True)
    notification_defaults = models.JSONField(default=dict, blank=True)
