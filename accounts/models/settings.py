from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class ThemePreference(models.TextChoices):
    SYSTEM = "system", "System"
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"


class CalendarSystem(models.TextChoices):
    GREGORIAN = "gregorian", "Gregorian"
    JALALI = "jalali", "Jalali"
    HIJRI = "hijri", "Hijri"


class UserSettings(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    theme = models.CharField(
        max_length=16,
        choices=ThemePreference.choices,
        default=ThemePreference.SYSTEM,
    )
    calendar_system = models.CharField(
        max_length=16,
        choices=CalendarSystem.choices,
        default=CalendarSystem.JALALI,
    )
    week_starts_on = models.PositiveSmallIntegerField(default=6)
    email_notifications_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    sms_notifications_enabled = models.BooleanField(default=False)
    marketing_emails_enabled = models.BooleanField(default=False)
    product_updates_enabled = models.BooleanField(default=True)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Settings for {self.user_id}"


class UserPreferences(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    daily_goal_minutes = models.PositiveIntegerField(default=120)
    weekly_goal_minutes = models.PositiveIntegerField(default=840)
    study_reminders_enabled = models.BooleanField(default=True)
    streak_reminders_enabled = models.BooleanField(default=True)
    preferred_study_times = models.JSONField(default=list, blank=True)
    content_language = models.CharField(max_length=16, default="fa")
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    default_study_mode = models.CharField(max_length=32, default="focus")

    def __str__(self) -> str:
        return f"Preferences for {self.user_id}"
