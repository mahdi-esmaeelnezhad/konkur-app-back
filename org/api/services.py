from __future__ import annotations

from django.utils import timezone

from coaching.api.services import build_student_progress_summary
from org.models import ParentChildRelationship, ParentChildRelationshipStatus


def build_child_summary(child_id) -> dict:
    progress = build_student_progress_summary(child_id)
    return {
        "child_id": str(child_id),
        "progress": progress,
    }


def create_parent_link_invite(parent, child_id, *, invited_at=None):
    invited_at = invited_at or timezone.now()
    relationship, created = ParentChildRelationship.objects.get_or_create(
        parent=parent,
        child_id=child_id,
        defaults={
            "status": ParentChildRelationshipStatus.PENDING,
            "invited_at": invited_at,
        },
    )
    if not created and relationship.status == ParentChildRelationshipStatus.REVOKED:
        relationship.status = ParentChildRelationshipStatus.PENDING
        relationship.invited_at = invited_at
        relationship.save(update_fields=["status", "invited_at", "updated_at"])
    return relationship


def accept_parent_link_invite(relationship: ParentChildRelationship, child_user) -> ParentChildRelationship:
    if relationship.child_id != child_user.id:
        raise PermissionError("Only the invited child can accept.")
    if relationship.status != ParentChildRelationshipStatus.PENDING:
        raise ValueError("Invite is not pending.")
    relationship.status = ParentChildRelationshipStatus.ACTIVE
    relationship.accepted_at = timezone.now()
    relationship.verified_at = timezone.now()
    relationship.save(update_fields=["status", "accepted_at", "verified_at", "updated_at"])
    return relationship
