from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class RankingPeriodKind(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    SEASON = "season", "Season"
    ALL_TIME = "all_time", "All time"


class RankingPeriod(TimeStampedModel):
    kind = models.CharField(max_length=16, choices=RankingPeriodKind.choices, db_index=True)
    period_key = models.CharField(max_length=64, db_index=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "period_key"],
                name="social_ranking_period_unique",
            ),
        ]


class RankingCategory(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    metric = models.CharField(max_length=64, db_index=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class RankingPrivacySetting(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ranking_privacy_settings",
    )
    category = models.ForeignKey(
        RankingCategory,
        on_delete=models.CASCADE,
        related_name="privacy_settings",
    )
    is_visible = models.BooleanField(default=True)
    show_real_name = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category"],
                name="social_ranking_privacy_unique",
            ),
        ]


class Leaderboard(TimeStampedModel):
    slug = models.SlugField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        RankingCategory,
        on_delete=models.PROTECT,
        related_name="leaderboards",
    )
    period_kind = models.CharField(
        max_length=16,
        choices=RankingPeriodKind.choices,
        db_index=True,
    )
    community = models.ForeignKey(
        "social.Community",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="leaderboards",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "period_kind", "is_active"]),
        ]


class LeaderboardSnapshot(TimeStampedModel):
    leaderboard = models.ForeignKey(
        Leaderboard,
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    period = models.ForeignKey(
        RankingPeriod,
        on_delete=models.PROTECT,
        related_name="leaderboard_snapshots",
    )
    computed_at = models.DateTimeField(db_index=True)
    entry_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["leaderboard", "period"],
                name="social_leaderboard_snapshot_unique_period",
            ),
        ]
        indexes = [
            models.Index(fields=["leaderboard", "-computed_at"]),
        ]


class LeaderboardEntry(TimeStampedModel):
    snapshot = models.ForeignKey(
        LeaderboardSnapshot,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leaderboard_entries",
    )
    rank = models.PositiveIntegerField()
    score = models.DecimalField(max_digits=18, decimal_places=4)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "user"],
                name="social_leaderboard_entry_unique_user",
            ),
            models.UniqueConstraint(
                fields=["snapshot", "rank"],
                name="social_leaderboard_entry_unique_rank",
            ),
        ]
        indexes = [
            models.Index(fields=["snapshot", "rank"]),
            models.Index(fields=["user", "-created_at"]),
        ]


class CompetitionSeasonStatus(models.TextChoices):
    UPCOMING = "upcoming", "Upcoming"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"


class CompetitionSeason(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=128, unique=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=16,
        choices=CompetitionSeasonStatus.choices,
        default=CompetitionSeasonStatus.UPCOMING,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["status", "starts_at"]),
        ]


class SeasonResult(TimeStampedModel):
    season = models.ForeignKey(
        CompetitionSeason,
        on_delete=models.CASCADE,
        related_name="results",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="season_results",
    )
    final_rank = models.PositiveIntegerField()
    final_score = models.DecimalField(max_digits=18, decimal_places=4)
    category = models.ForeignKey(
        RankingCategory,
        on_delete=models.PROTECT,
        related_name="season_results",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["season", "user", "category"],
                name="social_season_result_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["season", "final_rank"]),
        ]


class TeamCompetition(TimeStampedModel):
    season = models.ForeignKey(
        CompetitionSeason,
        on_delete=models.CASCADE,
        related_name="team_competitions",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=128)
    community = models.ForeignKey(
        "social.Community",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_competitions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["season", "slug"],
                name="social_team_competition_unique_slug",
            ),
        ]


class TeamCompetitionParticipant(TimeStampedModel):
    team = models.ForeignKey(
        TeamCompetition,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_competition_participations",
    )
    is_captain = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="social_team_competition_participant_unique",
            ),
        ]


class HallOfFameEntry(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hall_of_fame_entries",
    )
    season = models.ForeignKey(
        CompetitionSeason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hall_of_fame_entries",
    )
    category = models.ForeignKey(
        RankingCategory,
        on_delete=models.PROTECT,
        related_name="hall_of_fame_entries",
    )
    title = models.CharField(max_length=255)
    highlight = models.TextField(blank=True)
    rank_achieved = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]
