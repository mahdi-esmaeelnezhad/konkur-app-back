from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models.school import School, StudentClassEnrollment


class AssignmentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class Assignment(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assignments_created",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.DRAFT,
        db_index=True,
    )
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    max_score = models.PositiveIntegerField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status", "due_at"]),
        ]


class AssignmentTargetKind(models.TextChoices):
    CLASS = "class", "Class"
    STUDENT = "student", "Student"
    GRADE = "grade", "Grade"


class AssignmentTarget(TimeStampedModel):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="targets",
    )
    target_kind = models.CharField(max_length=32, choices=AssignmentTargetKind.choices)
    class_assignment = models.ForeignKey(
        "org.TeacherClassAssignment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assignment_targets",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assignment_targets",
    )
    grade_level = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "target_kind", "class_assignment", "student"],
                name="org_assignment_target_unique",
            ),
        ]


class AssignmentProgressStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not started"
    IN_PROGRESS = "in_progress", "In progress"
    SUBMITTED = "submitted", "Submitted"
    GRADED = "graded", "Graded"
    LATE = "late", "Late"


class AssignmentProgress(TimeStampedModel):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_progress",
    )
    enrollment = models.ForeignKey(
        StudentClassEnrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignment_progress",
    )
    status = models.CharField(
        max_length=32,
        choices=AssignmentProgressStatus.choices,
        default=AssignmentProgressStatus.NOT_STARTED,
        db_index=True,
    )
    score = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="org_assignment_progress_unique",
            ),
        ]
