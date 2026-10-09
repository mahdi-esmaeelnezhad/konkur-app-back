from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class CoachProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_profile",
    )
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    education_summary = models.TextField(blank=True)
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    student_capacity = models.PositiveIntegerField(default=30)
    active_student_count = models.PositiveIntegerField(default=0)
    is_accepting_students = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    specialties = models.ManyToManyField(
        "coaching.CoachSpecialty",
        related_name="coaches",
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["is_accepting_students", "-average_rating"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(active_student_count__lte=models.F("student_capacity")),
                name="coaching_profile_capacity_not_exceeded",
            ),
        ]


class CoachSpecialty(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class CoachExamSpecialty(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="exam_specialties",
    )
    exam = models.ForeignKey(
        "education.Exam",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="coach_specialties",
    )
    exam_slug = models.CharField(max_length=128, blank=True, db_index=True)
    label = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["coach", "exam"],
                condition=models.Q(exam__isnull=False),
                name="coaching_exam_specialty_unique_exam",
            ),
            models.UniqueConstraint(
                fields=["coach", "exam_slug"],
                condition=~models.Q(exam_slug=""),
                name="coaching_exam_specialty_unique_slug",
            ),
        ]


class CoachCredential(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="credentials",
    )
    title = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True)
    issued_year = models.PositiveSmallIntegerField(null=True, blank=True)
    document_url = models.URLField(max_length=2048, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "-created_at"]),
        ]


class CoachVerificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    NEEDS_INFO = "needs_info", "Needs information"


class CoachVerification(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    status = models.CharField(
        max_length=16,
        choices=CoachVerificationStatus.choices,
        default=CoachVerificationStatus.PENDING,
        db_index=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "-submitted_at"]),
            models.Index(fields=["status", "-submitted_at"]),
        ]


class LanguageProficiency(models.TextChoices):
    BASIC = "basic", "Basic"
    CONVERSATIONAL = "conversational", "Conversational"
    FLUENT = "fluent", "Fluent"
    NATIVE = "native", "Native"


class CoachLanguage(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="languages",
    )
    language_code = models.CharField(max_length=16, db_index=True)
    proficiency = models.CharField(max_length=16, choices=LanguageProficiency.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["coach", "language_code"],
                name="coaching_language_unique",
            ),
        ]
