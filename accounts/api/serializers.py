from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from accounts.models import (
    AccountDeletionRequest,
    ConsentType,
    UserBlock,
    UserConsent,
    UserDevice,
    UserPreferences,
    UserPrivacySettings,
    UserProfile,
    UserRole,
    UserRoleStatus,
    UserSettings,
)

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "display_name",
            "bio",
            "avatar_url",
            "cover_url",
            "birth_date",
            "country_code",
            "city",
            "website_url",
            "public_slug",
            "default_visibility",
        )


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = (
            "theme",
            "calendar_system",
            "week_starts_on",
            "email_notifications_enabled",
            "push_notifications_enabled",
            "sms_notifications_enabled",
            "marketing_emails_enabled",
            "product_updates_enabled",
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
        )


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = (
            "daily_goal_minutes",
            "weekly_goal_minutes",
            "study_reminders_enabled",
            "streak_reminders_enabled",
            "preferred_study_times",
            "content_language",
            "onboarding_completed_at",
            "default_study_mode",
        )


class UserPrivacySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPrivacySettings
        fields = (
            "profile_visibility",
            "show_online_status",
            "show_study_activity",
            "show_last_active",
            "allow_discovery",
            "allow_messages_from",
            "show_in_rankings",
            "show_email_on_profile",
            "show_phone_on_profile",
        )


class UserMeSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "locale",
            "timezone",
            "phone",
            "account_status",
            "verification_status",
            "email_verified_at",
            "phone_verified_at",
            "date_joined",
            "last_login",
            "profile",
        )
        read_only_fields = (
            "id",
            "account_status",
            "verification_status",
            "email_verified_at",
            "phone_verified_at",
            "date_joined",
            "last_login",
        )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        instance = super().update(instance, validated_data)
        if profile_data is not None:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()
        return instance


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    locale = serializers.CharField(max_length=16, required=False, allow_blank=True)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = (attrs.get("username") or "").strip() or (attrs.get("email") or "").strip()
        if not identifier:
            raise serializers.ValidationError(
                {"username": "Provide username or email."},
            )
        attrs["identifier"] = identifier
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value: str) -> str:
        validate_password(value, self.context.get("user"))
        return value

    def validate(self, attrs):
        user = self.context["user"]
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Incorrect password."})
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid user identifier."}) from None

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs["user"] = user
        return attrs


class UserRoleSerializer(serializers.ModelSerializer):
    role_slug = serializers.CharField(source="role.slug", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = UserRole
        fields = (
            "id",
            "role_slug",
            "role_name",
            "status",
            "is_primary",
            "expires_at",
            "created_at",
        )
        read_only_fields = fields


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = (
            "id",
            "platform",
            "device_fingerprint",
            "device_label",
            "app_version",
            "os_version",
            "push_token",
            "is_trusted",
            "is_active",
            "last_seen_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "is_trusted", "last_seen_at", "created_at", "updated_at")


class UserBlockSerializer(serializers.ModelSerializer):
    blocked_id = serializers.UUIDField(source="blocked.id", read_only=True)
    blocked_username = serializers.CharField(source="blocked.username", read_only=True)

    class Meta:
        model = UserBlock
        fields = (
            "id",
            "blocked_id",
            "blocked_username",
            "reason",
            "created_at",
        )
        read_only_fields = ("id", "blocked_id", "blocked_username", "created_at")


class UserBlockCreateSerializer(serializers.Serializer):
    blocked_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class AccountDeletionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountDeletionRequest
        fields = (
            "id",
            "status",
            "reason_code",
            "feedback",
            "scheduled_for",
            "anonymize_only",
            "created_at",
        )
        read_only_fields = fields


class AccountDeletionRequestCreateSerializer(serializers.Serializer):
    reason_code = serializers.CharField(required=False, allow_blank=True, default="")
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
    anonymize_only = serializers.BooleanField(required=False, default=False)


class UserConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConsent
        fields = (
            "id",
            "consent_type",
            "version",
            "accepted",
            "accepted_at",
            "metadata",
            "created_at",
        )
        read_only_fields = fields


class UserConsentGrantSerializer(serializers.Serializer):
    consent_type = serializers.ChoiceField(choices=ConsentType.choices)
    version = serializers.CharField(max_length=32)
    metadata = serializers.JSONField(required=False, default=dict)


class AuthUserSerializer(serializers.ModelSerializer):
    """Compact user payload returned from login/register."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "locale",
            "timezone",
            "account_status",
            "verification_status",
        )
        read_only_fields = fields
