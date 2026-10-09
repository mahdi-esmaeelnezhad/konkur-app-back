from django.urls import include, path
from rest_framework.routers import DefaultRouter

from social.api import views

router = DefaultRouter()
router.register(r"posts", views.PostViewSet, basename="social-post")
router.register(r"communities", views.CommunityViewSet, basename="social-community")

urlpatterns = [
    path(
        "posts/<uuid:post_pk>/comments/",
        views.PostCommentListCreateView.as_view(),
        name="social-post-comment-list",
    ),
    path(
        "posts/<uuid:post_pk>/comments/<uuid:comment_pk>/",
        views.PostCommentDestroyView.as_view(),
        name="social-post-comment-detail",
    ),
    path(
        "posts/<uuid:post_pk>/reactions/",
        views.PostReactionToggleView.as_view(),
        name="social-post-reactions",
    ),
    path(
        "posts/<uuid:post_pk>/save/",
        views.PostSaveView.as_view(),
        name="social-post-save",
    ),
    path("feed/", views.ActivityFeedListView.as_view(), name="social-feed"),
    path("follows/", views.FollowListCreateDestroyView.as_view(), name="social-follows"),
    path(
        "follows/following/",
        views.FollowingListView.as_view(),
        name="social-following",
    ),
    path(
        "follows/followers/",
        views.FollowersListView.as_view(),
        name="social-followers",
    ),
    path(
        "friend-requests/",
        views.FriendRequestListCreateView.as_view(),
        name="social-friend-request-list",
    ),
    path(
        "friend-requests/<uuid:pk>/accept/",
        views.FriendRequestAcceptView.as_view(),
        name="social-friend-request-accept",
    ),
    path(
        "friend-requests/<uuid:pk>/reject/",
        views.FriendRequestRejectView.as_view(),
        name="social-friend-request-reject",
    ),
    path(
        "friendships/",
        views.FriendshipListView.as_view(),
        name="social-friendship-list",
    ),
    path(
        "friendships/<uuid:pk>/",
        views.FriendshipDestroyView.as_view(),
        name="social-friendship-detail",
    ),
    path(
        "communities/<uuid:pk>/join/",
        views.CommunityJoinView.as_view(),
        name="social-community-join",
    ),
    path(
        "communities/<uuid:pk>/leave/",
        views.CommunityLeaveView.as_view(),
        name="social-community-leave",
    ),
    path("challenges/", views.ChallengeListView.as_view(), name="social-challenge-list"),
    path(
        "challenges/<uuid:pk>/join/",
        views.ChallengeJoinView.as_view(),
        name="social-challenge-join",
    ),
    path(
        "challenges/my/progress/",
        views.ChallengeMyProgressView.as_view(),
        name="social-challenge-my-progress",
    ),
    path(
        "leaderboards/<uuid:pk>/entries/",
        views.LeaderboardEntryListView.as_view(),
        name="social-leaderboard-entries",
    ),
    path(
        "xp/transactions/",
        views.XpTransactionListView.as_view(),
        name="social-xp-transactions",
    ),
    path("xp/level/", views.UserLevelView.as_view(), name="social-xp-level"),
    path(
        "achievements/",
        views.AchievementListView.as_view(),
        name="social-achievement-list",
    ),
    path(
        "achievements/unlocked/",
        views.MyAchievementListView.as_view(),
        name="social-achievement-unlocked",
    ),
    path("", include(router.urls)),
]
