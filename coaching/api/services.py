from __future__ import annotations

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from coaching.models import (
    CoachProfile,
    CoachStudentRelationship,
    CoachStudentRelationshipStatus,
    CoachStudentRequest,
    CoachStudentRequestStatus,
)
from study.models import DailyStudySummary, StreakRecord, StreakType


def get_or_create_coach_profile(user) -> CoachProfile:
    profile, _created = CoachProfile.objects.get_or_create(user=user)
    return profile


def build_student_progress_summary(student_id) -> dict:
    summaries = DailyStudySummary.objects.filter(user_id=student_id)
    last_7_days = summaries.order_by("-date")[:7]
    totals = summaries.aggregate(
        total_active_seconds=Sum("total_active_seconds"),
        total_sessions=Sum("session_count"),
        total_questions=Sum("questions_solved"),
    )
    streak = (
        StreakRecord.objects.filter(
            user_id=student_id,
            streak_type=StreakType.DAILY_STUDY,
        )
        .only("current_count", "longest_count", "last_activity_date")
        .first()
    )
    return {
        "student_id": str(student_id),
        "last_7_days": [
            {
                "date": row.date.isoformat(),
                "total_active_seconds": row.total_active_seconds,
                "session_count": row.session_count,
                "questions_solved": row.questions_solved,
            }
            for row in last_7_days
        ],
        "lifetime_totals": {
            "total_active_seconds": totals["total_active_seconds"] or 0,
            "total_sessions": totals["total_sessions"] or 0,
            "total_questions": totals["total_questions"] or 0,
        },
        "daily_study_streak": {
            "current_count": streak.current_count if streak else 0,
            "longest_count": streak.longest_count if streak else 0,
            "last_activity_date": (
                streak.last_activity_date.isoformat()
                if streak and streak.last_activity_date
                else None
            ),
        },
    }


@transaction.atomic
def accept_coach_student_request(request_obj: CoachStudentRequest, coach_user) -> CoachStudentRelationship:
    if request_obj.coach.user_id != coach_user.id:
        raise PermissionError("Only the coach can accept this request.")
    if request_obj.status != CoachStudentRequestStatus.PENDING:
        raise ValueError("Request is not pending.")

    request_obj.status = CoachStudentRequestStatus.ACCEPTED
    request_obj.save(update_fields=["status", "updated_at"])

    relationship, _created = CoachStudentRelationship.objects.get_or_create(
        coach=request_obj.coach,
        student=request_obj.student,
        defaults={"status": CoachStudentRelationshipStatus.ACTIVE},
    )
    if relationship.status != CoachStudentRelationshipStatus.ACTIVE:
        relationship.status = CoachStudentRelationshipStatus.ACTIVE
        relationship.ended_at = None
        relationship.save(update_fields=["status", "ended_at", "updated_at"])
    return relationship


def decline_coach_student_request(request_obj: CoachStudentRequest, coach_user) -> None:
    if request_obj.coach.user_id != coach_user.id:
        raise PermissionError("Only the coach can decline this request.")
    if request_obj.status != CoachStudentRequestStatus.PENDING:
        raise ValueError("Request is not pending.")
    request_obj.status = CoachStudentRequestStatus.DECLINED
    request_obj.save(update_fields=["status", "updated_at"])
