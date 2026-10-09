import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

from accounts.api import services
from accounts.api.serializers import (
    AccountDeletionRequestCreateSerializer,
    AccountDeletionRequestSerializer,
    AuthUserSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserBlockCreateSerializer,
    UserBlockSerializer,
    UserConsentGrantSerializer,
    UserConsentSerializer,
    UserDeviceSerializer,
    UserMeSerializer,
    UserPreferencesSerializer,
    UserPrivacySettingsSerializer,
    UserProfileSerializer,
    UserRoleSerializer,
    UserSettingsSerializer,
)
from accounts.models import (
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
from common.api.mixins import OwnershipQuerysetMixin, SuccessResponseMixin
from common.api.permissions import IsActiveAccount
from common.api.throttling import AuthThrottle

User = get_user_model()
logger = logging.getLogger(__name__)

ME_PERMISSIONS = (IsAuthenticated, IsActiveAccount)


class RegisterView(SuccessResponseMixin, APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AuthThrottle,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        locale = (data.get("locale") or "").strip() or None
        try:
            user, tokens = services.register_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                locale=locale,
                request=request,
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages) from exc

        payload = {
            **tokens,
            "user": AuthUserSerializer(user).data,
        }
        return self.success(payload, status=status.HTTP_201_CREATED)


class LoginView(SuccessResponseMixin, APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AuthThrottle,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.login_user(
            identifier=serializer.validated_data["identifier"],
            password=serializer.validated_data["password"],
            request=request,
        )
        if result is None:
            raise AuthenticationFailed("Invalid credentials.")
        user, tokens = result
        payload = {
            **tokens,
            "user": AuthUserSerializer(user).data,
        }
        return self.success(payload)


class LogoutView(SuccessResponseMixin, APIView):
    permission_classes = ME_PERMISSIONS

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_refresh = serializer.validated_data["refresh"]
        try:
            token = JWTRefreshToken(raw_refresh)
            token.blacklist()
        except TokenError as exc:
            raise ValidationError({"refresh": "Invalid or expired token."}) from exc
        services.revoke_stored_refresh(raw_refresh)
        return self.success({"detail": "Logged out."})


class TokenRefreshView(SuccessResponseMixin, SimpleJWTTokenRefreshView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response
        return self.success(response.data)


class PasswordChangeView(SuccessResponseMixin, APIView):
    permission_classes = ME_PERMISSIONS

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return self.success({"detail": "Password updated."})


class PasswordResetView(SuccessResponseMixin, APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            logger.info(
                "Password reset requested for user_id=%s uid=%s token=%s",
                user.pk,
                uid,
                token,
            )
        return self.success({"detail": "If an account exists, reset instructions were sent."})


class PasswordResetConfirmView(SuccessResponseMixin, APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return self.success({"detail": "Password has been reset."})


class MeView(SuccessResponseMixin, generics.RetrieveUpdateAPIView):
    permission_classes = ME_PERMISSIONS
    serializer_class = UserMeSerializer

    def get_object(self):
        user = self.request.user
        services.ensure_user_defaults(user)
        return user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.success(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self.success(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class _MeRelatedRetrieveUpdateView(SuccessResponseMixin, generics.RetrieveUpdateAPIView):
    permission_classes = ME_PERMISSIONS

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return self.success(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self.success(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class MeProfileView(_MeRelatedRetrieveUpdateView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class MeSettingsView(_MeRelatedRetrieveUpdateView):
    serializer_class = UserSettingsSerializer

    def get_object(self):
        settings_obj, _ = UserSettings.objects.get_or_create(user=self.request.user)
        return settings_obj


class MePreferencesView(_MeRelatedRetrieveUpdateView):
    serializer_class = UserPreferencesSerializer

    def get_object(self):
        prefs, _ = UserPreferences.objects.get_or_create(user=self.request.user)
        return prefs


class MePrivacyView(_MeRelatedRetrieveUpdateView):
    serializer_class = UserPrivacySettingsSerializer

    def get_object(self):
        privacy, _ = UserPrivacySettings.objects.get_or_create(user=self.request.user)
        return privacy


class MeRolesView(SuccessResponseMixin, generics.ListAPIView):
    permission_classes = ME_PERMISSIONS
    serializer_class = UserRoleSerializer

    def get_queryset(self):
        return (
            UserRole.objects.filter(user=self.request.user, status=UserRoleStatus.ACTIVE)
            .select_related("role")
            .order_by("-is_primary", "created_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)


class MeDeviceListCreateView(SuccessResponseMixin, OwnershipQuerysetMixin, generics.ListCreateAPIView):
    permission_classes = ME_PERMISSIONS
    serializer_class = UserDeviceSerializer
    queryset = UserDevice.objects.all()
    owner_field = "user"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return self.success(serializer.data, status=status.HTTP_201_CREATED)


class MeDeviceDestroyView(SuccessResponseMixin, OwnershipQuerysetMixin, generics.DestroyAPIView):
    permission_classes = ME_PERMISSIONS
    serializer_class = UserDeviceSerializer
    queryset = UserDevice.objects.all()
    owner_field = "user"
    lookup_field = "pk"
    lookup_url_kwarg = "device_id"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(None, status=status.HTTP_204_NO_CONTENT)


class MeBlockListCreateView(SuccessResponseMixin, OwnershipQuerysetMixin, generics.ListCreateAPIView):
    permission_classes = ME_PERMISSIONS
    queryset = UserBlock.objects.select_related("blocked").all()
    owner_field = "blocker"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserBlockCreateSerializer
        return UserBlockSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserBlockSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserBlockSerializer(queryset, many=True)
        return self.success(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = UserBlockCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blocked_id = serializer.validated_data["blocked_id"]
        if blocked_id == request.user.pk:
            raise ValidationError({"blocked_id": "You cannot block yourself."})
        try:
            blocked_user = User.objects.get(pk=blocked_id)
        except User.DoesNotExist as exc:
            raise ValidationError({"blocked_id": "User not found."}) from exc

        block, created = UserBlock.objects.get_or_create(
            blocker=request.user,
            blocked=blocked_user,
            defaults={"reason": serializer.validated_data.get("reason", "")},
        )
        if not created and serializer.validated_data.get("reason"):
            block.reason = serializer.validated_data["reason"]
            block.save(update_fields=["reason", "updated_at"])

        return self.success(
            UserBlockSerializer(block).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MeBlockDestroyView(SuccessResponseMixin, OwnershipQuerysetMixin, generics.DestroyAPIView):
    permission_classes = ME_PERMISSIONS
    serializer_class = UserBlockSerializer
    queryset = UserBlock.objects.all()
    owner_field = "blocker"
    lookup_field = "pk"
    lookup_url_kwarg = "block_id"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(None, status=status.HTTP_204_NO_CONTENT)


class MeDeletionRequestView(SuccessResponseMixin, APIView):
    permission_classes = ME_PERMISSIONS

    def post(self, request):
        serializer = AccountDeletionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deletion = services.create_deletion_request(
            request.user,
            reason_code=serializer.validated_data.get("reason_code", ""),
            feedback=serializer.validated_data.get("feedback", ""),
            anonymize_only=serializer.validated_data.get("anonymize_only", False),
        )
        return self.success(
            AccountDeletionRequestSerializer(deletion).data,
            status=status.HTTP_201_CREATED,
        )


class MeConsentListView(SuccessResponseMixin, OwnershipQuerysetMixin, generics.ListAPIView):
    permission_classes = ME_PERMISSIONS
    serializer_class = UserConsentSerializer
    queryset = UserConsent.objects.all()
    owner_field = "user"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)

    def post(self, request):
        serializer = UserConsentGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consent = services.grant_consent(
            request.user,
            consent_type=serializer.validated_data["consent_type"],
            version=serializer.validated_data["version"],
            request=request,
            metadata=serializer.validated_data.get("metadata"),
        )
        return self.success(UserConsentSerializer(consent).data, status=status.HTTP_201_CREATED)
