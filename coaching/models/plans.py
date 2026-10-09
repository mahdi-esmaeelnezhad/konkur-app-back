from django.db import models

from common.models import TimeStampedModel

from coaching.models.profile import CoachProfile


class CoachPlanTemplate(TimeStampedModel):
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.CASCADE,
        related_name="plan_templates",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "is_active"]),
        ]


class CoachPlanTemplateItemKind(models.TextChoices):
    STUDY = "study", "Study block"
    TEST = "test", "Practice test"
    REVIEW = "review", "Review"
    MEETING = "meeting", "Meeting"
    CUSTOM = "custom", "Custom"


class CoachPlanTemplateItem(TimeStampedModel):
    template = models.ForeignKey(
        CoachPlanTemplate,
        on_delete=models.CASCADE,
        related_name="items",
    )
    kind = models.CharField(max_length=16, choices=CoachPlanTemplateItemKind.choices)
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    day_offset = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["template", "sort_order"]),
        ]
