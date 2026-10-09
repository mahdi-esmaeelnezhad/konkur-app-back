from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel

from coaching.models.profile import CoachProfile


class CoachNote(SoftDeleteModel):
    """Private coach notes scoped to a coach–student pair; not visible to the student."""

    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="private_notes",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
    )
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "student", "-created_at"]),
        ]


class CoachAssignmentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ASSIGNED = "assigned", "Assigned"
    SUBMITTED = "submitted", "Submitted"
    REVIEWED = "reviewed", "Reviewed"
    CLOSED = "closed", "Closed"


class CoachAssignment(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_assignments",
    )
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=CoachAssignmentStatus.choices,
        default=CoachAssignmentStatus.ASSIGNED,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["student", "status", "due_at"]),
            models.Index(fields=["coach", "status", "-created_at"]),
        ]


class AssignmentSubmission(TimeStampedModel):
    assignment = models.ForeignKey(
        CoachAssignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    content = models.TextField(blank=True)
    attachment_url = models.URLField(max_length=2048, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="coaching_assignment_submission_unique",
            ),
        ]


class AssignmentFeedback(TimeStampedModel):
    submission = models.OneToOneField(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="assignment_feedback_given",
    )
    feedback = models.TextField()
    score = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "-created_at"]),
        ]


class CoachMeetingStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No show"


class CoachMeeting(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="meetings",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_meetings",
    )
    title = models.CharField(max_length=255, blank=True)
    scheduled_start = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(
        max_length=16,
        choices=CoachMeetingStatus.choices,
        default=CoachMeetingStatus.SCHEDULED,
        db_index=True,
    )
    meeting_url = models.URLField(max_length=2048, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "scheduled_start"]),
            models.Index(fields=["student", "scheduled_start"]),
        ]


class CoachMeetingNote(SoftDeleteModel):
    meeting = models.ForeignKey(
        CoachMeeting,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_meeting_notes_authored",
    )
    body = models.TextField()
    is_private = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["meeting", "-created_at"]),
        ]


class CoachReview(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_reviews_written",
    )
    relationship = models.ForeignKey(
        "coaching.CoachStudentRelationship",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["coach", "reviewer"],
                name="coaching_review_unique_reviewer",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="coaching_review_rating_range",
            ),
            models.CheckConstraint(
                condition=models.Q(relationship__isnull=False),
                name="coaching_review_requires_relationship",
            ),
        ]
        indexes = [
            models.Index(fields=["coach", "-created_at"]),
            models.Index(fields=["coach", "is_public", "-created_at"]),
        ]
