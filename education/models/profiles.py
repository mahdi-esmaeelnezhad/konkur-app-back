from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from education.models.exams import Exam, ExamSession
from education.models.institutions import Institution, Major, Program
from education.models.systems import EducationLevel, Grade


class UserEducationProfileStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    WITHDRAWN = "withdrawn", "Withdrawn"
    ON_LEAVE = "on_leave", "On leave"


class UserEducationProfile(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="education_profiles",
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )
    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )
    level = models.ForeignKey(
        EducationLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )
    status = models.CharField(
        max_length=32,
        choices=UserEducationProfileStatus.choices,
        default=UserEducationProfileStatus.ACTIVE,
        db_index=True,
    )
    is_primary = models.BooleanField(default=False, db_index=True)
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "user_education_profiles"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_primary=True),
                name="education_user_profile_primary_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["institution", "status"]),
        ]


class UserExamRegistrationStatus(models.TextChoices):
    REGISTERED = "registered", "Registered"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    WITHDRAWN = "withdrawn", "Withdrawn"
    CANCELLED = "cancelled", "Cancelled"


class UserExamRegistration(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_registrations",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="registrations",
    )
    status = models.CharField(
        max_length=32,
        choices=UserExamRegistrationStatus.choices,
        default=UserExamRegistrationStatus.REGISTERED,
        db_index=True,
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    external_registration_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
    )

    class Meta:
        db_table = "user_exam_registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "exam", "session"],
                condition=models.Q(session__isnull=False),
                name="education_user_exam_registration_session_unique",
            ),
            models.UniqueConstraint(
                fields=["user", "exam"],
                condition=models.Q(session__isnull=True),
                name="education_user_exam_registration_no_session_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["exam", "status"]),
        ]
