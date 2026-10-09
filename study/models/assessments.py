from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class TestDefinitionKind(models.TextChoices):
    PRACTICE = "practice", "Practice"
    MOCK = "mock", "Mock exam"
    OFFICIAL = "official", "Official"
    MANUAL_RECORD = "manual_record", "Manual record"


class TestAttemptStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    ABANDONED = "abandoned", "Abandoned"


class QuestionDifficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class TestDefinition(SoftDeleteModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_definitions",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    kind = models.CharField(
        max_length=24,
        choices=TestDefinitionKind.choices,
        default=TestDefinitionKind.PRACTICE,
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_definitions",
    )
    exam = models.ForeignKey(
        "education.Exam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_definitions",
    )
    total_questions = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = "tests"
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_test_definition_duration_non_negative",
            ),
        ]


class TestAttempt(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
    )
    test_definition = models.ForeignKey(
        TestDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
    )
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=16,
        choices=TestAttemptStatus.choices,
        default=TestAttemptStatus.IN_PROGRESS,
        db_index=True,
    )
    started_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    score_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(
        "education.Exam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_attempts",
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "test_attempts"
        indexes = [
            models.Index(fields=["user", "started_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_test_attempt_duration_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(correct_count__gte=0),
                name="study_test_attempt_correct_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(wrong_count__gte=0),
                name="study_test_attempt_wrong_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(unanswered_count__gte=0),
                name="study_test_attempt_unanswered_non_negative",
            ),
        ]


class TestSubjectResult(TimeStampedModel):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="subject_results",
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.CASCADE,
        related_name="test_subject_results",
    )
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    score_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "test_subject_results"
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "subject"],
                name="study_test_subject_result_unique",
            ),
        ]


class QuestionBank(SoftDeleteModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_banks",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_banks",
    )
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = "question_banks"


class Question(SoftDeleteModel):
    bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    stem = models.TextField()
    difficulty = models.CharField(
        max_length=16,
        choices=QuestionDifficulty.choices,
        default=QuestionDifficulty.MEDIUM,
        db_index=True,
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    topic = models.ForeignKey(
        "education.SubjectTopic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    explanation = models.TextField(blank=True)
    points = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "questions"
        indexes = [
            models.Index(fields=["bank", "difficulty"]),
        ]


class QuestionOption(TimeStampedModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )
    label = models.CharField(max_length=8)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "question_options"
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "label"],
                name="study_question_option_label_unique",
            ),
        ]


class QuestionTag(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        db_table = "question_tags"

    def __str__(self) -> str:
        return self.name


class QuestionTagLink(TimeStampedModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="tag_links",
    )
    tag = models.ForeignKey(
        QuestionTag,
        on_delete=models.CASCADE,
        related_name="question_links",
    )

    class Meta:
        db_table = "question_tag_links"
        constraints = [
            models.UniqueConstraint(
                fields=["question", "tag"],
                name="study_question_tag_link_unique",
            ),
        ]


class QuestionAttempt(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_attempts",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_attempts",
    )
    is_correct = models.BooleanField(null=True, blank=True)
    answered_at = models.DateTimeField(db_index=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "question_attempts"
        indexes = [
            models.Index(fields=["user", "answered_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_question_attempt_duration_non_negative",
            ),
        ]


class TestAttemptQuestion(TimeStampedModel):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="attempt_questions",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="test_attempt_questions",
    )
    sort_order = models.PositiveIntegerField(default=0)
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_attempt_questions",
    )
    is_correct = models.BooleanField(null=True, blank=True)
    is_answered = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "test_attempt_questions"
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="study_test_attempt_question_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(duration_seconds__gte=0),
                name="study_test_attempt_question_duration_non_negative",
            ),
        ]


class UserPerformanceSnapshot(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="performance_snapshots",
    )
    captured_at = models.DateTimeField(db_index=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)
    accuracy_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_performance_snapshots",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_performance_snapshots"
        indexes = [
            models.Index(fields=["user", "-captured_at"]),
        ]
