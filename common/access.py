"""Authorization helpers for privacy-aware data access.

API views and services MUST call these helpers. UI hiding is not authorization.
"""

from __future__ import annotations

from django.db.models import Q, QuerySet
from django.utils import timezone

from accounts.models import UserRole, UserRoleStatus
from org.models import (
    OrganizationMembership,
    OrganizationMembershipRole,
    ParentChildRelationship,
    ParentChildRelationshipStatus,
    ParentPermission,
    SchoolMembership,
    TeacherClassAssignment,
    TeacherProfile,
)


def user_has_active_role(user, role_slug: str) -> bool:
    now = timezone.now()
    return UserRole.objects.filter(
        user=user,
        role__slug=role_slug,
        status=UserRoleStatus.ACTIVE,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now)).exists()


def is_platform_admin(user) -> bool:
    return bool(getattr(user, "is_superuser", False)) or user_has_active_role(
        user, "platform_admin"
    )


def parent_can_view_child(
    parent_id,
    child_id,
    *,
    permission_code: str | None = None,
) -> bool:
    """Authorized child access only. Revoked/pending relationships deny immediately."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    parent_ok = User.objects.filter(pk=parent_id, account_status="active").exists()
    child_ok = User.objects.filter(pk=child_id, account_status="active").exists()
    if not parent_ok or not child_ok:
        return False

    rel = (
        ParentChildRelationship.objects.filter(
            parent_id=parent_id,
            child_id=child_id,
            status=ParentChildRelationshipStatus.ACTIVE,
        )
        .only("id")
        .first()
    )
    if rel is None:
        return False
    if permission_code is None:
        return True
    return ParentPermission.objects.filter(
        relationship=rel,
        permission=permission_code,
        granted=True,
    ).exists()


def coach_can_access_student(
    coach_user,
    student_id,
    *,
    allow_paused: bool = False,
) -> bool:
    from coaching.models import CoachProfile, CoachStudentRelationship

    profile = CoachProfile.objects.filter(user=coach_user).first()
    if profile is None:
        return False
    statuses = ["active"]
    if allow_paused:
        statuses.append("paused")
    return CoachStudentRelationship.objects.filter(
        coach=profile,
        student_id=student_id,
        status__in=statuses,
    ).exists()


def coach_notes_queryset_for_user(user) -> QuerySet:
    """Coach private notes are never readable by students or parents."""
    from coaching.models import CoachNote, CoachProfile

    profile = CoachProfile.objects.filter(user=user).first()
    if profile is None:
        return CoachNote.objects.none()
    return CoachNote.objects.filter(coach=profile)


def coach_notes_for_student_viewer(_student_user) -> QuerySet:
    """Students must never read coach private notes about themselves."""
    from coaching.models import CoachNote

    return CoachNote.objects.none()


def org_member_can(
    user,
    organization_id,
    *,
    min_roles: tuple[str, ...] | None = None,
) -> bool:
    qs = OrganizationMembership.objects.filter(
        user=user,
        organization_id=organization_id,
        status="active",
    )
    if min_roles:
        qs = qs.filter(role__in=min_roles)
    return qs.exists()


def org_admin_can_access(user, organization_id) -> bool:
    if is_platform_admin(user):
        return True
    return org_member_can(
        user,
        organization_id,
        min_roles=(
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        ),
    )


def school_member_can(user, school_id, *, roles: tuple[str, ...] | None = None) -> bool:
    qs = SchoolMembership.objects.filter(
        user=user,
        school_id=school_id,
        left_at__isnull=True,
    )
    if roles:
        qs = qs.filter(role__in=roles)
    return qs.exists()


def teacher_can_access_class(user, class_assignment_id) -> bool:
    profile = TeacherProfile.objects.filter(user=user).first()
    if profile is None:
        return False
    return TeacherClassAssignment.objects.filter(
        pk=class_assignment_id,
        teacher=profile,
    ).exists()


def conversation_messages_for_participant(user, conversation_id) -> QuerySet:
    from messaging.models import ConversationParticipant, Message

    is_member = ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user=user,
        left_at__isnull=True,
    ).exists()
    if not is_member:
        return Message.objects.none()
    return Message.objects.filter(conversation_id=conversation_id)


def user_is_blocked(viewer_id, other_id) -> bool:
    from accounts.models import UserBlock

    return UserBlock.objects.filter(
        blocker_id=viewer_id,
        blocked_id=other_id,
    ).exists() or UserBlock.objects.filter(
        blocker_id=other_id,
        blocked_id=viewer_id,
    ).exists()


def visible_posts_queryset_for(viewer) -> QuerySet:
    """Conservative feed filter: own posts + public/followers posts excluding blocks."""
    from accounts.models import UserBlock
    from social.models import Follow, Post, PostVisibility

    blocked_ids = set(
        UserBlock.objects.filter(blocker=viewer).values_list("blocked_id", flat=True)
    ) | set(UserBlock.objects.filter(blocked=viewer).values_list("blocker_id", flat=True))

    following_ids = set(
        Follow.objects.filter(follower=viewer).values_list("following_id", flat=True)
    )

    qs = Post.objects.all()
    if blocked_ids:
        qs = qs.exclude(author_id__in=blocked_ids)

    visibility_q = Q(author=viewer) | Q(visibility=PostVisibility.PUBLIC)
    if following_ids:
        visibility_q |= Q(
            visibility=PostVisibility.FOLLOWERS,
            author_id__in=following_ids,
        )
    return qs.filter(visibility_q)
