from rest_framework import serializers

from study.models import (
    DailyStudySummary,
    FocusSettings,
    Goal,
    GoalType,
    PomodoroSettings,
    StreakRecord,
    StudyPlan,
    StudyPlanItem,
    StudySession,
    StudySessionEvent,
    TestAttempt,
    TestDefinition,
)


class StudySessionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySessionEvent
        fields = (
            "id",
            "event_type",
            "occurred_at",
            "idempotency_key",
            "payload",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = (
            "id",
            "status",
            "source",
            "verification_status",
            "started_at",
            "ended_at",
            "active_seconds",
            "paused_seconds",
            "timezone",
            "activity_type",
            "subject",
            "topic",
            "goal",
            "planned_session",
            "plan_item",
            "exam",
            "title",
            "notes_summary",
            "questions_solved",
            "correct_answers",
            "wrong_answers",
            "is_pomodoro",
            "client_reported_seconds",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "source",
            "verification_status",
            "started_at",
            "ended_at",
            "active_seconds",
            "paused_seconds",
            "client_reported_seconds",
            "created_at",
            "updated_at",
        )


class StudySessionNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = ("notes_summary",)


class StudySessionStartSerializer(serializers.Serializer):
    timezone = serializers.CharField(max_length=64, required=False, default="UTC")
    activity_type = serializers.ChoiceField(
        choices=StudySession._meta.get_field("activity_type").choices,
        required=False,
    )
    subject = serializers.UUIDField(required=False, allow_null=True)
    topic = serializers.UUIDField(required=False, allow_null=True)
    goal = serializers.UUIDField(required=False, allow_null=True)
    planned_session = serializers.UUIDField(required=False, allow_null=True)
    plan_item = serializers.UUIDField(required=False, allow_null=True)
    exam = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    is_pomodoro = serializers.BooleanField(required=False, default=False)

    def to_session_data(self) -> dict:
        return dict(self.validated_data)


class ManualStudySessionCreateSerializer(serializers.Serializer):
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField()
    timezone = serializers.CharField(max_length=64, required=False, default="UTC")
    activity_type = serializers.ChoiceField(
        choices=StudySession._meta.get_field("activity_type").choices,
        required=False,
    )
    subject = serializers.UUIDField(required=False, allow_null=True)
    topic = serializers.UUIDField(required=False, allow_null=True)
    goal = serializers.UUIDField(required=False, allow_null=True)
    exam = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes_summary = serializers.CharField(required=False, allow_blank=True)
    questions_solved = serializers.IntegerField(required=False, min_value=0, default=0)
    correct_answers = serializers.IntegerField(required=False, min_value=0, default=0)
    wrong_answers = serializers.IntegerField(required=False, min_value=0, default=0)

    def to_session_data(self) -> dict:
        data = self.validated_data.copy()
        data.pop("started_at")
        data.pop("ended_at")
        return data


class StudySessionCompleteSerializer(serializers.Serializer):
    client_reported_seconds = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
    )


class GoalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalType
        fields = (
            "id",
            "code",
            "name",
            "description",
            "default_unit",
            "is_system",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = (
            "id",
            "goal_type",
            "title",
            "description",
            "target_value",
            "current_value",
            "unit",
            "status",
            "visibility",
            "deadline",
            "subject",
            "exam",
            "topic",
            "assigned_by",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "assigned_by", "completed_at", "created_at", "updated_at")


class StudyPlanItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPlanItem
        fields = (
            "id",
            "plan",
            "title",
            "description",
            "subject",
            "topic",
            "scheduled_date",
            "scheduled_start",
            "planned_duration_seconds",
            "priority",
            "sort_order",
            "is_completed",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "plan", "completed_at", "created_at", "updated_at")


class StudyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPlan
        fields = (
            "id",
            "title",
            "description",
            "status",
            "period",
            "period_start",
            "period_end",
            "timezone",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class DailyStudySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStudySummary
        fields = (
            "id",
            "date",
            "total_active_seconds",
            "session_count",
            "productive_seconds",
            "questions_solved",
            "goals_completed",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class StreakRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreakRecord
        fields = (
            "id",
            "streak_type",
            "current_count",
            "longest_count",
            "last_activity_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TestDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDefinition
        fields = (
            "id",
            "title",
            "description",
            "kind",
            "subject",
            "exam",
            "total_questions",
            "duration_seconds",
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAttempt
        fields = (
            "id",
            "test_definition",
            "title",
            "status",
            "started_at",
            "completed_at",
            "duration_seconds",
            "total_questions",
            "correct_count",
            "wrong_count",
            "unanswered_count",
            "score_percent",
            "exam",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class FocusSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FocusSettings
        fields = (
            "id",
            "block_distractions",
            "daily_limit_seconds",
            "session_limit_seconds",
            "auto_pause_on_idle",
            "idle_threshold_seconds",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class PomodoroSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PomodoroSettings
        fields = (
            "id",
            "work_seconds",
            "short_break_seconds",
            "long_break_seconds",
            "cycles_before_long_break",
            "auto_start_breaks",
            "auto_start_work",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
