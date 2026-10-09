from django.db import models

from common.models import TimeStampedModel

from education.models.geography import Country
from education.models.systems import EducationSystem


class ExamType(TimeStampedModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "exam_types"

    def __str__(self) -> str:
        return self.name


class Exam(TimeStampedModel):
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.PROTECT,
        related_name="exams",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exams",
    )
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exams",
    )
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "exams"
        indexes = [
            models.Index(fields=["exam_type", "is_active"]),
            models.Index(fields=["country", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name


class ExamSessionStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    REGISTRATION_OPEN = "registration_open", "Registration open"
    REGISTRATION_CLOSED = "registration_closed", "Registration closed"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class ExamSession(TimeStampedModel):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    code = models.SlugField(max_length=64)
    label = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=ExamSessionStatus.choices,
        default=ExamSessionStatus.SCHEDULED,
        db_index=True,
    )
    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exam_sessions"
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "code"],
                name="education_exam_session_exam_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["exam", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.exam.name} — {self.label}"


class ExamSubject(TimeStampedModel):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="exam_subjects",
    )
    subject = models.ForeignKey(
        "education.Subject",
        on_delete=models.CASCADE,
        related_name="exam_links",
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "exam_subjects"
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "subject"],
                name="education_exam_subject_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["exam", "sort_order"]),
        ]
        ordering = ["sort_order"]
