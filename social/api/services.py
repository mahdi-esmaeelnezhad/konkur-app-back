from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from common.access import user_is_blocked, visible_posts_queryset_for
from social.models import (
    Challenge,
    ChallengeParticipant,
    ChallengeParticipantStatus,
    ChallengeProgress,
    ChallengeStatus,
    Community,
    CommunityMembership,
    CommunityMembershipStatus,
    CommunityRole,
    CommunityRoleKind,
    CommunityVisibility,
    Follow,
    FriendRequest,
    FriendRequestStatus,
    Friendship,
    Leaderboard,
    LeaderboardEntry,
    LeaderboardSnapshot,
    Post,
    Reaction,
    SavedPost,
)

User = get_user_model()


def get_visible_post_or_404(viewer, post_id) -> Post:
    try:
        return visible_posts_queryset_for(viewer).get(pk=post_id)
    except Post.DoesNotExist as exc:
        raise NotFound("Post not found.") from exc


def get_owned_post_or_404(user, post_id) -> Post:
    try:
        return Post.objects.get(pk=post_id, author=user)
    except Post.DoesNotExist as exc:
        raise NotFound("Post not found.") from exc


def follow_user(follower, user_id):
    if str(follower.pk) == str(user_id):
        raise ValidationError({"user_id": "Cannot follow yourself."})
    try:
        target = User.objects.get(pk=user_id, account_status="active")
    except User.DoesNotExist as exc:
        raise NotFound("User not found.") from exc
    if user_is_blocked(follower.pk, target.pk):
        raise PermissionDenied("Cannot follow this user.")
    follow, created = Follow.objects.get_or_create(
        follower=follower,
        following=target,
    )
    return follow, created


def unfollow_user(follower, user_id):
    deleted, _ = Follow.objects.filter(follower=follower, following_id=user_id).delete()
    if not deleted:
        raise NotFound("Follow relationship not found.")
    return deleted


def create_friend_request(from_user, to_user_id, message=""):
    if str(from_user.pk) == str(to_user_id):
        raise ValidationError({"to_user_id": "Cannot send a friend request to yourself."})
    try:
        to_user = User.objects.get(pk=to_user_id, account_status="active")
    except User.DoesNotExist as exc:
        raise NotFound("User not found.") from exc
    if user_is_blocked(from_user.pk, to_user.pk):
        raise PermissionDenied("Cannot send a friend request to this user.")
    pair_a, pair_b = _friendship_pair(from_user.pk, to_user.pk)
    if Friendship.objects.filter(user_a_id=pair_a, user_b_id=pair_b).exists():
        raise ValidationError("You are already friends with this user.")
    if FriendRequest.objects.filter(
        from_user=from_user,
        to_user=to_user,
        status=FriendRequestStatus.PENDING,
    ).exists():
        raise ValidationError("A pending friend request already exists.")
    return FriendRequest.objects.create(
        from_user=from_user,
        to_user=to_user,
        message=message or "",
    )


def _friendship_pair(user_a_id, user_b_id):
    low, high = sorted([user_a_id, user_b_id], key=str)
    return low, high


@transaction.atomic
def accept_friend_request(recipient, request_id):
    try:
        fr = FriendRequest.objects.select_for_update().get(
            pk=request_id,
            to_user=recipient,
            status=FriendRequestStatus.PENDING,
        )
    except FriendRequest.DoesNotExist as exc:
        raise NotFound("Friend request not found.") from exc
    fr.status = FriendRequestStatus.ACCEPTED
    fr.save(update_fields=["status", "updated_at"])
    user_a_id, user_b_id = _friendship_pair(fr.from_user_id, fr.to_user_id)
    Friendship.objects.get_or_create(user_a_id=user_a_id, user_b_id=user_b_id)
    return fr


def reject_friend_request(recipient, request_id):
    try:
        fr = FriendRequest.objects.get(
            pk=request_id,
            to_user=recipient,
            status=FriendRequestStatus.PENDING,
        )
    except FriendRequest.DoesNotExist as exc:
        raise NotFound("Friend request not found.") from exc
    fr.status = FriendRequestStatus.DECLINED
    fr.save(update_fields=["status", "updated_at"])
    return fr


def remove_friendship(user, friendship_id):
    try:
        friendship = Friendship.objects.get(pk=friendship_id)
    except Friendship.DoesNotExist as exc:
        raise NotFound("Friendship not found.") from exc
    if user.pk not in (friendship.user_a_id, friendship.user_b_id):
        raise PermissionDenied("Not allowed to remove this friendship.")
    friendship.delete()
    return friendship


def toggle_post_reaction(user, post: Post, kind: str):
    existing = Reaction.objects.filter(user=user, post=post).first()
    if existing is None:
        return Reaction.objects.create(user=user, post=post, kind=kind), "created"
    if existing.kind == kind:
        existing.delete()
        return None, "removed"
    existing.kind = kind
    existing.save(update_fields=["kind", "updated_at"])
    return existing, "updated"


def remove_post_reaction(user, post: Post):
    deleted, _ = Reaction.objects.filter(user=user, post=post).delete()
    if not deleted:
        raise NotFound("Reaction not found.")
    return deleted


def save_post(user, post: Post):
    saved, created = SavedPost.objects.get_or_create(user=user, post=post)
    return saved, created


def unsave_post(user, post: Post):
    deleted, _ = SavedPost.objects.filter(user=user, post=post).delete()
    if not deleted:
        raise NotFound("Saved post not found.")
    return deleted


def _member_role_for(community: Community) -> CommunityRole:
    role = CommunityRole.objects.filter(
        community=community,
        kind=CommunityRoleKind.MEMBER,
    ).first()
    if role is None:
        role = CommunityRole.objects.create(
            community=community,
            kind=CommunityRoleKind.MEMBER,
            name="Member",
        )
    return role


def join_community(user, community_id):
    try:
        community = Community.objects.get(pk=community_id)
    except Community.DoesNotExist as exc:
        raise NotFound("Community not found.") from exc
    if community.visibility == CommunityVisibility.PRIVATE:
        raise PermissionDenied("This community is private.")
    membership, created = CommunityMembership.objects.get_or_create(
        community=community,
        user=user,
        defaults={
            "role": _member_role_for(community),
            "status": CommunityMembershipStatus.ACTIVE,
        },
    )
    if not created and membership.status == CommunityMembershipStatus.LEFT:
        membership.status = CommunityMembershipStatus.ACTIVE
        membership.role = _member_role_for(community)
        membership.save(update_fields=["status", "role", "updated_at"])
        created = True
    return membership, created


def leave_community(user, community_id):
    try:
        membership = CommunityMembership.objects.get(
            community_id=community_id,
            user=user,
            status=CommunityMembershipStatus.ACTIVE,
        )
    except CommunityMembership.DoesNotExist as exc:
        raise NotFound("Membership not found.") from exc
    if membership.community.owner_id == user.pk:
        raise ValidationError("Community owners cannot leave; transfer ownership first.")
    membership.status = CommunityMembershipStatus.LEFT
    membership.save(update_fields=["status", "updated_at"])
    return membership


def join_challenge(user, challenge_id):
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist as exc:
        raise NotFound("Challenge not found.") from exc
    if challenge.status not in (ChallengeStatus.ACTIVE, ChallengeStatus.DRAFT):
        raise ValidationError("This challenge is not open for joining.")
    participant, created = ChallengeParticipant.objects.get_or_create(
        challenge=challenge,
        user=user,
        defaults={"status": ChallengeParticipantStatus.ACTIVE},
    )
    if not created and participant.status == ChallengeParticipantStatus.WITHDRAWN:
        participant.status = ChallengeParticipantStatus.ACTIVE
        participant.save(update_fields=["status", "updated_at"])
        created = True
    return participant, created


def leaderboard_entries_for(leaderboard_id):
    try:
        leaderboard = Leaderboard.objects.get(pk=leaderboard_id, is_active=True)
    except Leaderboard.DoesNotExist as exc:
        raise NotFound("Leaderboard not found.") from exc
    snapshot = (
        LeaderboardSnapshot.objects.filter(leaderboard=leaderboard)
        .order_by("-computed_at")
        .first()
    )
    if snapshot is None:
        return leaderboard, LeaderboardEntry.objects.none()
    return leaderboard, LeaderboardEntry.objects.filter(snapshot=snapshot).order_by("rank")


def user_challenge_progress(user):
    participants = ChallengeParticipant.objects.filter(
        user=user,
        status__in=(
            ChallengeParticipantStatus.ACTIVE,
            ChallengeParticipantStatus.COMPLETED,
        ),
    ).select_related("challenge")
    participant_ids = list(participants.values_list("pk", flat=True))
    progress = ChallengeProgress.objects.filter(
        participant_id__in=participant_ids
    ).select_related("participant", "goal")
    return participants, progress
