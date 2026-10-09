from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.access import visible_posts_queryset_for
from common.api.mixins import OwnershipQuerysetMixin
from common.api.permissions import IsActiveAccount, IsOwnerOrReadOnly
from social.api import services
from social.api.serializers import (
    AchievementSerializer,
    ActivityFeedItemSerializer,
    ChallengeParticipantSerializer,
    ChallengeProgressSerializer,
    ChallengeSerializer,
    CommentSerializer,
    CommunitySerializer,
    FollowActionSerializer,
    FollowSerializer,
    FriendRequestCreateSerializer,
    FriendRequestSerializer,
    FriendshipSerializer,
    LeaderboardEntrySerializer,
    PostSerializer,
    ReactionSerializer,
    ReactionToggleSerializer,
    SavedPostSerializer,
    UserAchievementSerializer,
    UserLevelSerializer,
    XpTransactionSerializer,
)
from social.models import (
    Achievement,
    ActivityFeedItem,
    Challenge,
    ChallengeStatus,
    Comment,
    Community,
    CommunityVisibility,
    Follow,
    FriendRequest,
    FriendRequestStatus,
    Friendship,
    Post,
    UserAchievement,
    UserLevel,
    XpTransaction,
)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsActiveAccount, IsOwnerOrReadOnly]
    owner_field = "author"
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Post.objects.none()
        return visible_posts_queryset_for(user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.pk:
            raise PermissionDenied("Only the author can delete this post.")
        instance.delete()


class PostCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = CommentSerializer

    def get_queryset(self):
        post = services.get_visible_post_or_404(self.request.user, self.kwargs["post_pk"])
        return Comment.objects.filter(post=post).order_by("created_at")

    def perform_create(self, serializer):
        post = services.get_visible_post_or_404(self.request.user, self.kwargs["post_pk"])
        serializer.save(author=self.request.user, post=post)


class PostCommentDestroyView(generics.DestroyAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = CommentSerializer
    lookup_url_kwarg = "comment_pk"

    def get_queryset(self):
        post = services.get_visible_post_or_404(self.request.user, self.kwargs["post_pk"])
        return Comment.objects.filter(post=post)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.pk:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()


class PostReactionToggleView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, post_pk):
        post = services.get_visible_post_or_404(request.user, post_pk)
        serializer = ReactionToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction, action = services.toggle_post_reaction(
            request.user,
            post,
            serializer.validated_data["kind"],
        )
        if action == "removed":
            return Response(status=status.HTTP_204_NO_CONTENT)
        code = status.HTTP_201_CREATED if action == "created" else status.HTTP_200_OK
        return Response(ReactionSerializer(reaction).data, status=code)

    def delete(self, request, post_pk):
        post = services.get_visible_post_or_404(request.user, post_pk)
        services.remove_post_reaction(request.user, post)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostSaveView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, post_pk):
        post = services.get_visible_post_or_404(request.user, post_pk)
        saved, created = services.save_post(request.user, post)
        return Response(
            SavedPostSerializer(saved).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, post_pk):
        post = services.get_visible_post_or_404(request.user, post_pk)
        services.unsave_post(request.user, post)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActivityFeedListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = ActivityFeedItemSerializer

    def get_queryset(self):
        return ActivityFeedItem.objects.filter(recipient=self.request.user).order_by(
            "-created_at"
        )


class FollowListCreateDestroyView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        serializer = FollowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        follow, created = services.follow_user(
            request.user,
            serializer.validated_data["user_id"],
        )
        return Response(
            FollowSerializer(follow).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        serializer = FollowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.unfollow_user(request.user, serializer.validated_data["user_id"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowingListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return (
            Follow.objects.filter(follower=self.request.user)
            .select_related("following")
            .order_by("-created_at")
        )


class FollowersListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return (
            Follow.objects.filter(following=self.request.user)
            .select_related("follower")
            .order_by("-created_at")
        )


class FriendRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsActiveAccount]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FriendRequestCreateSerializer
        return FriendRequestSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            FriendRequest.objects.filter(
                Q(from_user=user) | Q(to_user=user),
                status=FriendRequestStatus.PENDING,
            )
            .select_related("from_user", "to_user")
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = FriendRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fr = services.create_friend_request(
            request.user,
            serializer.validated_data["to_user_id"],
            message=serializer.validated_data.get("message", ""),
        )
        return Response(
            FriendRequestSerializer(fr).data,
            status=status.HTTP_201_CREATED,
        )


class FriendRequestAcceptView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, pk):
        fr = services.accept_friend_request(request.user, pk)
        return Response(FriendRequestSerializer(fr).data)


class FriendRequestRejectView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, pk):
        fr = services.reject_friend_request(request.user, pk)
        return Response(FriendRequestSerializer(fr).data)


class FriendshipListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = FriendshipSerializer

    def get_queryset(self):
        user = self.request.user
        return Friendship.objects.filter(Q(user_a=user) | Q(user_b=user)).order_by(
            "-created_at"
        )


class FriendshipDestroyView(generics.DestroyAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = FriendshipSerializer
    queryset = Friendship.objects.all()

    def perform_destroy(self, instance):
        services.remove_friendship(self.request.user, instance.pk)


class CommunityViewSet(viewsets.ModelViewSet):
    serializer_class = CommunitySerializer
    permission_classes = [IsActiveAccount]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        return (
            Community.objects.filter(
                Q(visibility=CommunityVisibility.PUBLIC)
                | Q(owner=user)
                | Q(memberships__user=user, memberships__status="active")
            )
            .distinct()
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        community = self.get_object()
        if community.owner_id != request.user.pk:
            raise PermissionDenied("Only the community owner can update this community.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        community = self.get_object()
        if community.owner_id != request.user.pk:
            raise PermissionDenied("Only the community owner can update this community.")
        return super().partial_update(request, *args, **kwargs)


class CommunityJoinView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, pk):
        membership, created = services.join_community(request.user, pk)
        community = membership.community
        return Response(
            CommunitySerializer(community).data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )


class CommunityLeaveView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, pk):
        services.leave_community(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChallengeListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = ChallengeSerializer

    def get_queryset(self):
        return Challenge.objects.exclude(status=ChallengeStatus.CANCELLED).order_by(
            "-starts_at"
        )


class ChallengeJoinView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, pk):
        participant, created = services.join_challenge(request.user, pk)
        return Response(
            ChallengeParticipantSerializer(participant).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ChallengeMyProgressView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = ChallengeProgressSerializer

    def get_queryset(self):
        _participants, progress = services.user_challenge_progress(self.request.user)
        return progress.order_by("-recorded_at")


class LeaderboardEntryListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = LeaderboardEntrySerializer

    def get_queryset(self):
        _board, entries = services.leaderboard_entries_for(self.kwargs["pk"])
        return entries


class XpTransactionListView(OwnershipQuerysetMixin, generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = XpTransactionSerializer
    queryset = XpTransaction.objects.all().order_by("-created_at")


class UserLevelView(generics.RetrieveAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = UserLevelSerializer

    def get_object(self):
        try:
            return UserLevel.objects.select_related("current_level").get(
                user=self.request.user
            )
        except UserLevel.DoesNotExist as exc:
            raise NotFound("Level profile not found.") from exc


class AchievementListView(generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = AchievementSerializer
    queryset = Achievement.objects.filter(is_active=True).order_by("title")


class MyAchievementListView(OwnershipQuerysetMixin, generics.ListAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = UserAchievementSerializer
    queryset = UserAchievement.objects.all().select_related("achievement").order_by(
        "-earned_at"
    )
