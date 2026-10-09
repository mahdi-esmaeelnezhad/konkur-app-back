from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models.organization import Organization


class SchoolStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class School(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="schools",
        null=True,
        blank=True,
        help_text="Required for tenant schools; null only for legacy/unscoped records.",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64)
    status = models.CharField(
        max_length=32,
        choices=SchoolStatus.choices,
        default=SchoolStatus.ACTIVE,
        db_index=True,
    )
    address = models.TextField(blank=True, default="")
    timezone = models.CharField(max_length=64, default="UTC")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "slug"],
                condition=models.Q(organization__isnull=False),
                name="org_school_org_slug_unique",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(organization__isnull=True),
                name="org_school_unscoped_slug_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self) -> str:
        return self.name


class SchoolMembershipRole(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    COUNSELOR = "counselor", "Counselor"
    ADMIN = "admin", "Admin"


class SchoolMembership(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="school_memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=SchoolMembershipRole.choices,
        db_index=True,
    )
    external_student_id = models.CharField(max_length=64, blank=True, default="")
    enrolled_at = models.DateField(null=True, blank=True)
    left_at = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user"],
                name="org_school_membership_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "role"]),
        ]


class TeacherProfile(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profiles",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="teachers",
    )
    employee_id = models.CharField(max_length=64, blank=True, default="")
    title = models.CharField(max_length=128, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user"],
                name="org_teacher_profile_school_user_unique",
            ),
        ]


class TeacherClassAssignment(TimeStampedModel):
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="class_assignments",
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="class_assignments",
    )
    class_name = models.CharField(max_length=128)
    section = models.CharField(max_length=32, blank=True, default="")
    subject_name = models.CharField(max_length=128)
    academic_year = models.CharField(max_length=16, db_index=True)
    grade_level = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "teacher",
                    "school",
                    "class_name",
                    "section",
                    "subject_name",
                    "academic_year",
                ],
                name="org_teacher_class_assignment_unique",
            ),
        ]


class StudentClassEnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    TRANSFERRED = "transferred", "Transferred"
    DROPPED = "dropped", "Dropped"


class StudentClassEnrollment(TimeStampedModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="class_enrollments",
    )
    class_assignment = models.ForeignKey(
        TeacherClassAssignment,
        on_delete=models.CASCADE,
        related_name="student_enrollments",
    )
    status = models.CharField(
        max_length=32,
        choices=StudentClassEnrollmentStatus.choices,
        default=StudentClassEnrollmentStatus.ACTIVE,
        db_index=True,
    )
    enrolled_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "class_assignment"],
                name="org_student_class_enrollment_unique",
            ),
        ]
