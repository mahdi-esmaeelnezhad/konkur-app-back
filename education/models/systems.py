from django.db import models

from common.models import TimeStampedModel

from education.models.geography import Country


class EducationSystem(TimeStampedModel):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="education_systems",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "education_systems"
        constraints = [
            models.UniqueConstraint(
                fields=["country", "code"],
                name="education_system_country_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["country", "is_active", "sort_order"]),
        ]
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class EducationLevel(TimeStampedModel):
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.CASCADE,
        related_name="levels",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=128)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "education_levels"
        constraints = [
            models.UniqueConstraint(
                fields=["education_system", "code"],
                name="education_level_system_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["education_system", "is_active", "sort_order"]),
        ]
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Grade(TimeStampedModel):
    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE,
        related_name="grades",
    )
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=128)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "grades"
        constraints = [
            models.UniqueConstraint(
                fields=["education_level", "code"],
                name="education_grade_level_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["education_level", "is_active", "sort_order"]),
        ]
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class AcademicYear(TimeStampedModel):
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.CASCADE,
        related_name="academic_years",
    )
    code = models.SlugField(max_length=32)
    label = models.CharField(max_length=128)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "academic_years"
        constraints = [
            models.UniqueConstraint(
                fields=["education_system", "code"],
                name="education_academic_year_system_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["education_system", "is_current"]),
        ]

    def __str__(self) -> str:
        return self.label
