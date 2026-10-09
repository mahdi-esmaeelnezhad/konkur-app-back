from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class PostVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    FOLLOWERS = "followers", "Followers"
    FRIENDS = "friends", "Friends"
    PRIVATE = "private", "Private"
    COMMUNITY = "community", "Community only"


class PostType(models.TextChoices):
    TEXT = "text", "Text"
    SESSION = "session", "Study session"
    STREAK = "streak", "Streak"
    GOAL = "goal", "Goal"
    CHALLENGE = "challenge", "Challenge"
    ACHIEVEMENT = "achievement", "Achievement"
    MEDIA = "media", "Media"


class Post(SoftDeleteModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    post_type = models.CharField(
        max_length=24,
        choices=PostType.choices,
        default=PostType.TEXT,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=16,
        choices=PostVisibility.choices,
        default=PostVisibility.FOLLOWERS,
        db_index=True,
    )
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    community = models.ForeignKey(
        "social.Community",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    comment_count = models.PositiveIntegerField(default=0)
    reaction_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["visibility", "-published_at"]),
            models.Index(fields=["community", "-published_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    ~models.Q(visibility=PostVisibility.COMMUNITY)
                    | models.Q(community__isnull=False)
                ),
                name="social_post_community_visibility_requires_community",
            ),
        ]


class PostAttachmentKind(models.TextChoices):
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"
    FILE = "file", "File"
    LINK = "link", "Link"


class PostAttachment(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    kind = models.CharField(max_length=16, choices=PostAttachmentKind.choices)
    url = models.URLField(max_length=2048)
    mime_type = models.CharField(max_length=128, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["post", "sort_order"]),
        ]


class Comment(SoftDeleteModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )
    body = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]


class ReactionKind(models.TextChoices):
    LIKE = "like", "Like"
    CELEBRATE = "celebrate", "Celebrate"
    SUPPORT = "support", "Support"
    INSIGHTFUL = "insightful", "Insightful"


class Reaction(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_reactions",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reactions",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reactions",
    )
    kind = models.CharField(max_length=16, choices=ReactionKind.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                condition=models.Q(post__isnull=False),
                name="social_reaction_unique_user_post",
            ),
            models.UniqueConstraint(
                fields=["user", "comment"],
                condition=models.Q(comment__isnull=False),
                name="social_reaction_unique_user_comment",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(post__isnull=False, comment__isnull=True)
                    | models.Q(post__isnull=True, comment__isnull=False)
                ),
                name="social_reaction_single_target",
            ),
        ]
        indexes = [
            models.Index(fields=["post", "kind"]),
            models.Index(fields=["comment", "kind"]),
        ]


class PostShare(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_shares",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    caption = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["post", "-created_at"]),
        ]


class ActivityFeedVerb(models.TextChoices):
    POST_CREATED = "post_created", "Post created"
    POST_SHARED = "post_shared", "Post shared"
    CHALLENGE_JOINED = "challenge_joined", "Challenge joined"
    ACHIEVEMENT_EARNED = "achievement_earned", "Achievement earned"
    COMMUNITY_JOINED = "community_joined", "Community joined"


class ActivityFeedItem(TimeStampedModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_feed_items",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_feed_actions",
    )
    verb = models.CharField(max_length=32, choices=ActivityFeedVerb.choices, db_index=True)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feed_items",
    )
    visibility_snapshot = models.CharField(
        max_length=16,
        choices=PostVisibility.choices,
        default=PostVisibility.PRIVATE,
    )
    dedupe_key = models.CharField(max_length=128, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "dedupe_key"],
                condition=models.Q(dedupe_key__isnull=False),
                name="social_feed_item_unique_dedupe",
            ),
        ]


class SavedPost(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_posts",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="saved_by",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="social_saved_post_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]


class Hashtag(TimeStampedModel):
    tag = models.CharField(max_length=100, unique=True)
    normalized_tag = models.CharField(max_length=100, unique=True, db_index=True)
    use_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["-use_count"]),
        ]


class PostHashtag(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_hashtags",
    )
    hashtag = models.ForeignKey(
        Hashtag,
        on_delete=models.CASCADE,
        related_name="post_links",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "hashtag"],
                name="social_post_hashtag_unique",
            ),
        ]
