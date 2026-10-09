from django.db import models

from common.models import TimeStampedModel

from education.models.geography import Country
from education.models.systems import EducationSystem


class InstitutionType(TimeStampedModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "institution_types"

    def __str__(self) -> str:
        return self.name


class InstitutionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending", "Pending verification"


class Institution(TimeStampedModel):
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="institutions",
    )
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.PROTECT,
        related_name="institutions",
    )
    institution_type = models.ForeignKey(
        InstitutionType,
        on_delete=models.PROTECT,
        related_name="institutions",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64)
    status = models.CharField(
        max_length=32,
        choices=InstitutionStatus.choices,
        default=InstitutionStatus.ACTIVE,
        db_index=True,
    )
    city = models.CharField(max_length=128, blank=True, default="")
    website = models.URLField(max_length=2048, blank=True, default="")

    class Meta:
        db_table = "institutions"
        constraints = [
            models.UniqueConstraint(
                fields=["education_system", "slug"],
                name="education_institution_system_slug_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["country", "status"]),
            models.Index(fields=["education_system", "status"]),
        ]

    def __str__(self) -> str:
        return self.name


class Faculty(TimeStampedModel):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="faculties",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "faculties"
        verbose_name_plural = "Faculties"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="education_faculty_institution_code_unique",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Department(TimeStampedModel):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="departments",
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="departments",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "departments"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="education_department_institution_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["institution", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name


class Program(TimeStampedModel):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="programs",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    degree_label = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "programs"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "code"],
                name="education_program_department_code_unique",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Major(TimeStampedModel):
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="majors",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "majors"
        constraints = [
            models.UniqueConstraint(
                fields=["program", "code"],
                name="education_major_program_code_unique",
            ),
        ]

    def __str__(self) -> str:
        return self.name
