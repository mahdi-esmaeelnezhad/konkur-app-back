from django.conf import settings
from django.db import models

from common.models import TimeStampedModel

from org.models.school import School, StudentClassEnrollment


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    EXCUSED = "excused", "Excused"


class AttendanceRecord(TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    enrollment = models.ForeignKey(
        StudentClassEnrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )
    session_date = models.DateField(db_index=True)
    status = models.CharField(max_length=16, choices=AttendanceStatus.choices)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_recorded",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "student", "session_date", "enrollment"],
                name="org_attendance_record_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "session_date"]),
        ]
