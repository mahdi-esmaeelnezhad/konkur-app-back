from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class PlatformSetting(TimeStampedModel):
    key = models.CharField(max_length=128, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.key


class FeatureFlag(TimeStampedModel):
    key = models.CharField(max_length=128, unique=True)
    enabled = models.BooleanField(default=False, db_index=True)
    description = models.TextField(blank=True, default="")
    rules = models.JSONField(default=dict, blank=True)
    rollout_percentage = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rollout_percentage__lte=100),
                name="platformcfg_feature_flag_rollout_lte_100",
            ),
        ]


class SupportedLocale(TimeStampedModel):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=128)
    native_name = models.CharField(max_length=128, blank=True, default="")
    is_rtl = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "code"]


class SupportedCurrency(TimeStampedModel):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=128)
    symbol = models.CharField(max_length=8, blank=True, default="")
    minor_unit = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name_plural = "Supported currencies"


class CalendarSystem(models.TextChoices):
    GREGORIAN = "gregorian", "Gregorian"
    JALALI = "jalali", "Jalali"
    HIJRI = "hijri", "Hijri"


class CalendarPreference(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_preference",
    )
    calendar_system = models.CharField(
        max_length=16,
        choices=CalendarSystem.choices,
        default=CalendarSystem.JALALI,
    )
    week_starts_on = models.PositiveSmallIntegerField(default=6)
    is_global_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_global_default"],
                condition=models.Q(is_global_default=True, user__isnull=True),
                name="platformcfg_calendar_global_default_unique",
            ),
        ]


class SystemAnnouncementSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    CRITICAL = "critical", "Critical"


class SystemAnnouncement(TimeStampedModel):
    title = models.CharField(max_length=255)
    body = models.TextField()
    severity = models.CharField(
        max_length=16,
        choices=SystemAnnouncementSeverity.choices,
        default=SystemAnnouncementSeverity.INFO,
    )
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    target_locales = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "starts_at"]),
        ]


class AdminRole(TimeStampedModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    permissions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class AdminRoleAssignment(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_role_assignments",
    )
    role = models.ForeignKey(
        AdminRole,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_roles_granted",
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="platformcfg_admin_role_assignment_unique",
            ),
        ]


class PlatformAnalyticsSnapshot(TimeStampedModel):
    snapshot_date = models.DateField(unique=True, db_index=True)
    metrics = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)


class DataRetentionPolicy(TimeStampedModel):
    entity_type = models.CharField(max_length=64, unique=True)
    retention_days = models.PositiveIntegerField()
    hard_delete_after_days = models.PositiveIntegerField(null=True, blank=True)
    anonymize_on_delete = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Data retention policies"


class ScheduledJobCheckpoint(TimeStampedModel):
    job_name = models.CharField(max_length=128, db_index=True)
    period_key = models.CharField(max_length=128)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    cursor = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job_name", "period_key"],
                name="platformcfg_scheduled_job_checkpoint_unique",
            ),
        ]
