from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class PortfolioItemKind(models.TextChoices):
    ACHIEVEMENT = "achievement", "Achievement"
    PROJECT = "project", "Project"
    TEST_SCORE = "test_score", "Test score"
    NOTE = "note", "Note"
    CUSTOM = "custom", "Custom"


class AcademicPortfolio(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_portfolio",
    )
    headline = models.CharField(max_length=255, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=False)
    public_slug = models.SlugField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_public"]),
        ]


class PortfolioItem(TimeStampedModel):
    portfolio = models.ForeignKey(
        AcademicPortfolio,
        on_delete=models.CASCADE,
        related_name="items",
    )
    kind = models.CharField(max_length=32, choices=PortfolioItemKind.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    occurred_on = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["portfolio", "sort_order"]),
        ]
        ordering = ["sort_order", "-created_at"]


class AcademicMilestoneKind(models.TextChoices):
    EXAM_PASSED = "exam_passed", "Exam passed"
    GRADE_PROMOTED = "grade_promoted", "Grade promoted"
    STREAK = "streak", "Study streak"
    CHALLENGE = "challenge", "Challenge completed"
    CUSTOM = "custom", "Custom"


class AcademicMilestone(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_milestones",
    )
    kind = models.CharField(max_length=32, choices=AcademicMilestoneKind.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    achieved_at = models.DateTimeField(db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "achieved_at"]),
        ]


class ShareableAchievementCard(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shareable_achievement_cards",
    )
    slug = models.SlugField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    card_data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]


class AnnualRecapSnapshot(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="annual_recap_snapshots",
    )
    year = models.PositiveSmallIntegerField()
    stats = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "year"],
                name="portfolio_annual_recap_user_year_unique",
            ),
        ]
