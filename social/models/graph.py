from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class FriendRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    CANCELLED = "cancelled", "Cancelled"


class Follow(TimeStampedModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_set",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_set",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="social_follow_unique_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("following")),
                name="social_follow_not_self",
            ),
        ]
        indexes = [
            models.Index(fields=["follower", "created_at"]),
            models.Index(fields=["following", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.follower_id} → {self.following_id}"


class FriendRequest(TimeStampedModel):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_received",
    )
    status = models.CharField(
        max_length=16,
        choices=FriendRequestStatus.choices,
        default=FriendRequestStatus.PENDING,
        db_index=True,
    )
    message = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"],
                condition=models.Q(status=FriendRequestStatus.PENDING),
                name="social_friend_request_unique_pending",
            ),
            models.CheckConstraint(
                condition=~models.Q(from_user=models.F("to_user")),
                name="social_friend_request_not_self",
            ),
        ]
        indexes = [
            models.Index(fields=["to_user", "status", "created_at"]),
        ]


class Friendship(TimeStampedModel):
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_as_a",
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_as_b",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_a", "user_b"],
                name="social_friendship_unique_pair",
            ),
            models.CheckConstraint(
                condition=models.Q(user_a_id__lt=models.F("user_b_id")),
                name="social_friendship_ordered_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["user_a"]),
            models.Index(fields=["user_b"]),
        ]
