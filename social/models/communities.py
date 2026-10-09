from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel, TimeStampedModel


class CommunityVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    PRIVATE = "private", "Private"
    INVITE_ONLY = "invite_only", "Invite only"


class CommunityType(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Community(SoftDeleteModel):
    community_type = models.ForeignKey(
        CommunityType,
        on_delete=models.PROTECT,
        related_name="communities",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_communities",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=16,
        choices=CommunityVisibility.choices,
        default=CommunityVisibility.PUBLIC,
        db_index=True,
    )
    avatar_url = models.URLField(max_length=2048, blank=True)
    banner_url = models.URLField(max_length=2048, blank=True)
    is_verified = models.BooleanField(default=False)
    member_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "communities"
        indexes = [
            models.Index(fields=["visibility", "-created_at"]),
            models.Index(fields=["community_type", "-member_count"]),
        ]


class CommunityRoleKind(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MODERATOR = "moderator", "Moderator"
    MEMBER = "member", "Member"


class CommunityRole(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    kind = models.CharField(max_length=16, choices=CommunityRoleKind.choices)
    name = models.CharField(max_length=64, blank=True)
    permissions = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["community", "kind"],
                name="social_community_role_unique_kind",
            ),
        ]


class CommunityMembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    MUTED = "muted", "Muted"
    BANNED = "banned", "Banned"
    LEFT = "left", "Left"


class CommunityMembership(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_memberships",
    )
    role = models.ForeignKey(
        CommunityRole,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    status = models.CharField(
        max_length=16,
        choices=CommunityMembershipStatus.choices,
        default=CommunityMembershipStatus.ACTIVE,
        db_index=True,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["community", "user"],
                name="social_community_membership_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["community", "status"]),
        ]


class CommunityInvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


class CommunityInvitation(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_invitations_sent",
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="community_invitations_received",
    )
    invitee_email = models.EmailField(blank=True)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=CommunityInvitationStatus.choices,
        default=CommunityInvitationStatus.PENDING,
        db_index=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["community", "status"]),
        ]


class CommunityRule(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["community", "sort_order"]),
        ]


class CommunityPost(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )
    post = models.OneToOneField(
        "social.Post",
        on_delete=models.CASCADE,
        related_name="community_link",
    )
    is_pinned = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["community", "is_pinned", "-created_at"]),
        ]


class CommunityModerator(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="moderators",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_moderator_roles",
    )
    appointed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_moderator_appointments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["community", "user"],
                name="social_community_moderator_unique",
            ),
        ]


class CommunityEvent(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="events",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=512, blank=True)
    is_online = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["community", "starts_at"]),
        ]


class CommunityResourceKind(models.TextChoices):
    LINK = "link", "Link"
    DOCUMENT = "document", "Document"
    VIDEO = "video", "Video"


class CommunityResource(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="resources",
    )
    title = models.CharField(max_length=255)
    kind = models.CharField(max_length=16, choices=CommunityResourceKind.choices)
    url = models.URLField(max_length=2048)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_resources_uploaded",
    )

    class Meta:
        indexes = [
            models.Index(fields=["community", "-created_at"]),
        ]


class StudyGroup(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="study_groups",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_study_groups",
    )
    max_members = models.PositiveIntegerField(default=50)

    class Meta:
        indexes = [
            models.Index(fields=["community", "-created_at"]),
        ]


class StudyGroupMembershipRole(models.TextChoices):
    OWNER = "owner", "Owner"
    MEMBER = "member", "Member"


class StudyGroupMembership(TimeStampedModel):
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_group_memberships",
    )
    role = models.CharField(
        max_length=16,
        choices=StudyGroupMembershipRole.choices,
        default=StudyGroupMembershipRole.MEMBER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["study_group", "user"],
                name="social_study_group_membership_unique",
            ),
        ]


class StudyGroupGoal(TimeStampedModel):
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="goals",
    )
    title = models.CharField(max_length=255)
    target_value = models.PositiveIntegerField()
    unit = models.CharField(max_length=32)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["study_group", "deadline"]),
        ]


class StudyGroupSession(TimeStampedModel):
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    scheduled_start = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hosted_study_group_sessions",
    )

    class Meta:
        indexes = [
            models.Index(fields=["study_group", "scheduled_start"]),
        ]


class CommunityMilestone(TimeStampedModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    threshold_value = models.PositiveIntegerField()
    achieved_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["community", "-achieved_at"]),
        ]
