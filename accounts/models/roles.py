from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class RoleSlug(models.TextChoices):
    STUDENT = "student", "Student"
    COACH = "coach", "Coach"
    PARENT = "parent", "Parent"
    TEACHER = "teacher", "Teacher"
    SCHOOL_ADMIN = "school_admin", "School administrator"
    ORG_ADMIN = "org_admin", "Organization administrator"
    COMMUNITY_MODERATOR = "community_moderator", "Community moderator"
    PLATFORM_ADMIN = "platform_admin", "Platform administrator"


class Role(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True, choices=RoleSlug.choices)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    is_system = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "slug"]

    def __str__(self) -> str:
        return self.name


class Permission(TimeStampedModel):
    codename = models.SlugField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    module = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        ordering = ["module", "codename"]

    def __str__(self) -> str:
        return self.codename


class RolePermission(TimeStampedModel):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="accounts_role_permission_unique",
            ),
        ]


class UserRoleStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class UserRole(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    status = models.CharField(
        max_length=16,
        choices=UserRoleStatus.choices,
        default=UserRoleStatus.ACTIVE,
        db_index=True,
    )
    is_primary = models.BooleanField(default=False)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roles_granted",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="accounts_user_role_unique",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_primary=True, status=UserRoleStatus.ACTIVE),
                name="accounts_user_primary_role_unique",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_primary=False)
                    | models.Q(status=UserRoleStatus.ACTIVE)
                ),
                name="accounts_user_primary_requires_active",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["role", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.role_id} ({self.status})"
