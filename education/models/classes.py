from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from education.models.institutions import Institution
from education.models.systems import AcademicYear, Grade


class ClassGroupStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class ClassGroup(TimeStampedModel):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="class_groups",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="class_groups",
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_groups",
    )
    name = models.CharField(max_length=128)
    section = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=ClassGroupStatus.choices,
        default=ClassGroupStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        db_table = "classes"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "academic_year", "name", "section"],
                name="education_class_group_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "academic_year", "status"]),
        ]

    def __str__(self) -> str:
        if self.section:
            return f"{self.name} ({self.section})"
        return self.name


class ClassMembershipRole(models.TextChoices):
    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    HOMEROOM = "homeroom", "Homeroom teacher"
    ASSISTANT = "assistant", "Assistant"


class ClassMembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    TRANSFERRED = "transferred", "Transferred"
    DROPPED = "dropped", "Dropped"


class ClassMembership(TimeStampedModel):
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="class_memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=ClassMembershipRole.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=ClassMembershipStatus.choices,
        default=ClassMembershipStatus.ACTIVE,
        db_index=True,
    )
    enrolled_on = models.DateField(null=True, blank=True)
    left_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "class_memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["class_group", "user"],
                name="education_class_membership_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["class_group", "role"]),
        ]
