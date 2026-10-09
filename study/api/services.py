from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from common.api.exceptions import ConflictError
from study.models import (
    StudySession,
    StudySessionEvent,
    StudySessionEventType,
    StudySessionSource,
    StudySessionStatus,
)

LIVE_STATUSES = (StudySessionStatus.ACTIVE, StudySessionStatus.PAUSED)
MIN_MANUAL_SESSION_SECONDS = 1
MAX_MANUAL_SESSION_SECONDS = 86400
CLIENT_DURATION_WALL_CLOCK_FACTOR = 1.2


def _segment_start_for_active(session: StudySession) -> datetime:
    last = (
        session.events.filter(
            event_type__in=(
                StudySessionEventType.START,
                StudySessionEventType.RESUME,
            )
        )
        .order_by("-occurred_at")
        .values_list("occurred_at", flat=True)
        .first()
    )
    if last is not None:
        return last
    if session.started_at is not None:
        return session.started_at
    return timezone.now()


def _last_pause_at(session: StudySession) -> datetime | None:
    return (
        session.events.filter(event_type=StudySessionEventType.PAUSE)
        .order_by("-occurred_at")
        .values_list("occurred_at", flat=True)
        .first()
    )


def _create_event(
    session: StudySession,
    event_type: str,
    *,
    occurred_at: datetime | None = None,
    idempotency_key: str | None = None,
    payload: dict | None = None,
) -> StudySessionEvent:
    return StudySessionEvent.objects.create(
        session=session,
        event_type=event_type,
        occurred_at=occurred_at or timezone.now(),
        idempotency_key=idempotency_key,
        payload=payload or {},
    )


def _lock_live_session(user) -> StudySession | None:
    return (
        StudySession.objects.select_for_update()
        .filter(user=user, status__in=LIVE_STATUSES)
        .first()
    )


def _get_owned_session_for_update(session_id, user) -> StudySession:
    try:
        return StudySession.objects.select_for_update().get(pk=session_id, user=user)
    except StudySession.DoesNotExist as exc:
        raise NotFound("Study session not found.") from exc


class StudySessionService:
    @staticmethod
    @transaction.atomic
    def start_session(user, **data: Any) -> StudySession:
        if _lock_live_session(user) is not None:
            raise ConflictError("You already have an active or paused study session.")

        now = timezone.now()
        session = StudySession.objects.create(
            user=user,
            status=StudySessionStatus.ACTIVE,
            source=StudySessionSource.TIMER,
            started_at=now,
            **data,
        )
        _create_event(session, StudySessionEventType.START, occurred_at=now)
        return session

    @staticmethod
    @transaction.atomic
    def pause_session(session: StudySession, user) -> StudySession:
        session = _get_owned_session_for_update(session.pk, user)
        if session.status != StudySessionStatus.ACTIVE:
            raise ValidationError("Only an active session can be paused.")

        now = timezone.now()
        segment_start = _segment_start_for_active(session)
        session.active_seconds += max(0, int((now - segment_start).total_seconds()))
        session.status = StudySessionStatus.PAUSED
        session.save(update_fields=["active_seconds", "status", "updated_at"])
        _create_event(session, StudySessionEventType.PAUSE, occurred_at=now)
        return session

    @staticmethod
    @transaction.atomic
    def resume_session(session: StudySession, user) -> StudySession:
        session = _get_owned_session_for_update(session.pk, user)
        if session.status != StudySessionStatus.PAUSED:
            raise ValidationError("Only a paused session can be resumed.")

        now = timezone.now()
        pause_at = _last_pause_at(session)
        if pause_at is not None:
            session.paused_seconds += max(0, int((now - pause_at).total_seconds()))
        session.status = StudySessionStatus.ACTIVE
        session.save(update_fields=["paused_seconds", "status", "updated_at"])
        _create_event(session, StudySessionEventType.RESUME, occurred_at=now)
        return session

    @staticmethod
    @transaction.atomic
    def complete_session(
        session: StudySession,
        user,
        *,
        client_reported_seconds: int | None = None,
    ) -> StudySession:
        session = _get_owned_session_for_update(session.pk, user)
        if session.status not in LIVE_STATUSES:
            raise ValidationError("Only an active or paused session can be completed.")

        now = timezone.now()
        if session.status == StudySessionStatus.ACTIVE:
            segment_start = _segment_start_for_active(session)
            session.active_seconds += max(0, int((now - segment_start).total_seconds()))
        elif session.status == StudySessionStatus.PAUSED:
            pause_at = _last_pause_at(session)
            if pause_at is not None:
                session.paused_seconds += max(0, int((now - pause_at).total_seconds()))

        if client_reported_seconds is not None and session.started_at is not None:
            wall_seconds = max(0, int((now - session.started_at).total_seconds()))
            cap = int(wall_seconds * CLIENT_DURATION_WALL_CLOCK_FACTOR)
            if client_reported_seconds <= cap:
                session.client_reported_seconds = client_reported_seconds

        session.ended_at = now
        session.status = StudySessionStatus.COMPLETED
        session.save(
            update_fields=[
                "active_seconds",
                "paused_seconds",
                "client_reported_seconds",
                "ended_at",
                "status",
                "updated_at",
            ]
        )
        _create_event(session, StudySessionEventType.COMPLETE, occurred_at=now)
        return session

    @staticmethod
    @transaction.atomic
    def cancel_session(session: StudySession, user) -> StudySession:
        session = _get_owned_session_for_update(session.pk, user)
        if session.status not in LIVE_STATUSES:
            raise ValidationError("Only an active or paused session can be cancelled.")

        now = timezone.now()
        if session.status == StudySessionStatus.ACTIVE:
            segment_start = _segment_start_for_active(session)
            session.active_seconds += max(0, int((now - segment_start).total_seconds()))
        elif session.status == StudySessionStatus.PAUSED:
            pause_at = _last_pause_at(session)
            if pause_at is not None:
                session.paused_seconds += max(0, int((now - pause_at).total_seconds()))

        session.ended_at = now
        session.status = StudySessionStatus.CANCELLED
        session.save(
            update_fields=[
                "active_seconds",
                "paused_seconds",
                "ended_at",
                "status",
                "updated_at",
            ]
        )
        _create_event(session, StudySessionEventType.CANCEL, occurred_at=now)
        return session

    @staticmethod
    @transaction.atomic
    def log_manual_session(
        user,
        *,
        started_at: datetime,
        ended_at: datetime,
        **data: Any,
    ) -> StudySession:
        if ended_at < started_at:
            raise ValidationError("ended_at must be greater than or equal to started_at.")

        duration = int((ended_at - started_at).total_seconds())
        if duration < MIN_MANUAL_SESSION_SECONDS:
            raise ValidationError(
                f"Session duration must be at least {MIN_MANUAL_SESSION_SECONDS} seconds."
            )
        if duration > MAX_MANUAL_SESSION_SECONDS:
            raise ValidationError(
                f"Session duration cannot exceed {MAX_MANUAL_SESSION_SECONDS} seconds."
            )

        session = StudySession.objects.create(
            user=user,
            status=StudySessionStatus.COMPLETED,
            source=StudySessionSource.MANUAL,
            started_at=started_at,
            ended_at=ended_at,
            active_seconds=duration,
            **data,
        )
        _create_event(
            session,
            StudySessionEventType.START,
            occurred_at=started_at,
        )
        _create_event(
            session,
            StudySessionEventType.COMPLETE,
            occurred_at=ended_at,
        )
        return session
