from django.db import models

from common.models import TimeStampedModel

from education.models.exams import Exam
from education.models.systems import EducationSystem


class Subject(TimeStampedModel):
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subjects",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subjects",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "subjects"
        constraints = [
            models.UniqueConstraint(
                fields=["education_system", "code"],
                condition=models.Q(education_system__isnull=False),
                name="education_subject_system_code_unique",
            ),
            models.UniqueConstraint(
                fields=["exam", "code"],
                condition=models.Q(exam__isnull=False),
                name="education_subject_exam_code_unique",
            ),
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(
                    education_system__isnull=True,
                    exam__isnull=True,
                ),
                name="education_subject_global_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class SubjectTopic(TimeStampedModel):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "subject_topics"
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "code"],
                name="education_subject_topic_subject_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["subject", "is_active", "sort_order"]),
        ]
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name
