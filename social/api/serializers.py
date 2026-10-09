from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.api.public_serializers import UserPublicSerializer
from social.models import (
    Achievement,
    ActivityFeedItem,
    Challenge,
    ChallengeParticipant,
    ChallengeProgress,
    Comment,
    Community,
    CommunityType,
    Follow,
    FriendRequest,
    Friendship,
    LeaderboardEntry,
    LevelDefinition,
    Post,
    Reaction,
    SavedPost,
    UserAchievement,
    UserLevel,
    XpTransaction,
)

User = get_user_model()


class PostSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "post_type",
            "visibility",
            "title",
            "body",
            "community",
            "published_at",
            "comment_count",
            "reaction_count",
            "share_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "comment_count",
            "reaction_count",
            "share_count",
            "created_at",
            "updated_at",
        )


class CommentSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "parent",
            "body",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "post", "author", "created_at", "updated_at")


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ("id", "user", "post", "kind", "created_at", "updated_at")
        read_only_fields = ("id", "user", "post", "created_at", "updated_at")


class ReactionToggleSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Reaction._meta.get_field("kind").choices)


class SavedPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPost
        fields = ("id", "user", "post", "created_at", "updated_at")
        read_only_fields = fields


class ActivityFeedItemSerializer(serializers.ModelSerializer):
    actor = UserPublicSerializer(read_only=True)

    class Meta:
        model = ActivityFeedItem
        fields = (
            "id",
            "recipient",
            "actor",
            "verb",
            "post",
            "visibility_snapshot",
            "payload",
            "is_read",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class FollowSerializer(serializers.ModelSerializer):
    follower = UserPublicSerializer(read_only=True)
    following = UserPublicSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at", "updated_at")
        read_only_fields = fields


class FollowActionSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserPublicSerializer(read_only=True)
    to_user = UserPublicSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = (
            "id",
            "from_user",
            "to_user",
            "status",
            "message",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "from_user",
            "to_user",
            "status",
            "created_at",
            "updated_at",
        )


class FriendRequestCreateSerializer(serializers.Serializer):
    to_user_id = serializers.UUIDField()
    message = serializers.CharField(required=False, allow_blank=True, default="")


class FriendshipSerializer(serializers.ModelSerializer):
    user_a = UserPublicSerializer(read_only=True)
    user_b = UserPublicSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ("id", "user_a", "user_b", "created_at", "updated_at")
        read_only_fields = fields


class CommunityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityType
        fields = ("id", "slug", "name", "description", "created_at", "updated_at")
        read_only_fields = fields


class CommunitySerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)

    class Meta:
        model = Community
        fields = (
            "id",
            "community_type",
            "owner",
            "name",
            "slug",
            "description",
            "visibility",
            "avatar_url",
            "banner_url",
            "is_verified",
            "member_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "is_verified",
            "member_count",
            "created_at",
            "updated_at",
        )


class ChallengeSerializer(serializers.ModelSerializer):
    creator = UserPublicSerializer(read_only=True)

    class Meta:
        model = Challenge
        fields = (
            "id",
            "creator",
            "community",
            "title",
            "description",
            "metric",
            "target_value",
            "unit",
            "starts_at",
            "ends_at",
            "status",
            "xp_reward",
            "badge_name",
            "participant_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "creator",
            "participant_count",
            "created_at",
            "updated_at",
        )


class ChallengeParticipantSerializer(serializers.ModelSerializer):
    challenge = ChallengeSerializer(read_only=True)

    class Meta:
        model = ChallengeParticipant
        fields = (
            "id",
            "challenge",
            "user",
            "status",
            "joined_at",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ChallengeProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeProgress
        fields = (
            "id",
            "participant",
            "goal",
            "current_value",
            "recorded_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = LeaderboardEntry
        fields = (
            "id",
            "snapshot",
            "user",
            "rank",
            "score",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class XpTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XpTransaction
        fields = (
            "id",
            "user",
            "amount",
            "source_type",
            "source_id",
            "description",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class LevelDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelDefinition
        fields = ("id", "level", "xp_required", "title", "created_at", "updated_at")
        read_only_fields = fields


class UserLevelSerializer(serializers.ModelSerializer):
    current_level = LevelDefinitionSerializer(read_only=True)

    class Meta:
        model = UserLevel
        fields = (
            "id",
            "user",
            "current_level",
            "current_xp",
            "lifetime_xp",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "icon_url",
            "xp_reward",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ("id", "user", "achievement", "earned_at", "created_at", "updated_at")
        read_only_fields = fields
