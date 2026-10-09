from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone as dt_timezone
from typing import TYPE_CHECKING

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken

from accounts.models import (
    AccountDeletionRequest,
    AccountDeletionStatus,
    AccountStatus,
    Role,
    RoleSlug,
    User,
    UserConsent,
    UserPreferences,
    UserPrivacySettings,
    UserProfile,
    UserRole,
    UserRoleStatus,
    UserSettings,
)
from accounts.models.tokens import RefreshToken as StoredRefreshToken

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def ensure_user_defaults(user: User) -> None:
    UserProfile.objects.get_or_create(user=user)
    UserSettings.objects.get_or_create(user=user)
    UserPreferences.objects.get_or_create(user=user)
    UserPrivacySettings.objects.get_or_create(user=user)


def assign_default_student_role(user: User) -> None:
    role = Role.objects.filter(slug=RoleSlug.STUDENT, is_active=True).first()
    if not role:
        return
    UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={
            "status": UserRoleStatus.ACTIVE,
            "is_primary": True,
        },
    )


def persist_refresh_token(
    user: User,
    raw_refresh: str,
    *,
    request: HttpRequest | None = None,
    device=None,
) -> None:
    try:
        jwt_refresh = JWTRefreshToken(raw_refresh)
        exp = jwt_refresh.get("exp")
        if exp is None:
            return
        expires_at = datetime.fromtimestamp(exp, tz=dt_timezone.utc)
    except Exception:
        logger.debug("Could not parse refresh token for persistence", exc_info=True)
        return

    ip_address = None
    user_agent = ""
    if request is not None:
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip_address = xff.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

    StoredRefreshToken.objects.update_or_create(
        token_hash=hash_refresh_token(raw_refresh),
        defaults={
            "user": user,
            "expires_at": expires_at,
            "revoked_at": None,
            "device": device,
            "ip_address": ip_address,
            "user_agent": user_agent,
        },
    )


def build_token_pair(user: User, *, request: HttpRequest | None = None, persist: bool = True) -> dict[str, str]:
    refresh = JWTRefreshToken.for_user(user)
    access = refresh.access_token
    data = {"access": str(access), "refresh": str(refresh)}
    if persist:
        persist_refresh_token(user, data["refresh"], request=request)
    return data


@transaction.atomic
def register_user(
    *,
    username: str,
    email: str,
    password: str,
    locale: str | None = None,
    request: HttpRequest | None = None,
) -> tuple[User, dict[str, str]]:
    validate_password(password)
    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError({"username": ["A user with that username already exists."]})
    if email and User.objects.filter(email__iexact=email).exists():
        raise ValidationError({"email": ["A user with that email already exists."]})

    user = User(
        username=username,
        email=email,
        account_status=AccountStatus.ACTIVE,
    )
    if locale:
        user.locale = locale
    user.set_password(password)
    user.save()

    ensure_user_defaults(user)
    assign_default_student_role(user)

    tokens = build_token_pair(user, request=request)
    return user, tokens


def resolve_user_by_identifier(identifier: str) -> User | None:
    ident = identifier.strip()
    if not ident:
        return None
    return User.objects.filter(Q(username__iexact=ident) | Q(email__iexact=ident)).first()


def login_user(
    *,
    identifier: str,
    password: str,
    request: HttpRequest | None = None,
) -> tuple[User, dict[str, str]] | None:
    user = resolve_user_by_identifier(identifier)
    if user is None:
        return None
    if user.account_status not in {AccountStatus.ACTIVE, AccountStatus.PENDING}:
        return None
    authenticated = authenticate(username=user.username, password=password)
    if authenticated is None:
        return None
    ensure_user_defaults(authenticated)
    tokens = build_token_pair(authenticated, request=request)
    return authenticated, tokens


def revoke_stored_refresh(raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    StoredRefreshToken.objects.filter(token_hash=token_hash, revoked_at__isnull=True).update(
        revoked_at=timezone.now(),
    )


def create_deletion_request(
    user: User,
    *,
    reason_code: str = "",
    feedback: str = "",
    anonymize_only: bool = False,
) -> AccountDeletionRequest:
    existing = AccountDeletionRequest.objects.filter(
        user=user,
        status__in={
            AccountDeletionStatus.PENDING,
            AccountDeletionStatus.SCHEDULED,
            AccountDeletionStatus.PROCESSING,
        },
    ).first()
    if existing:
        return existing
    return AccountDeletionRequest.objects.create(
        user=user,
        status=AccountDeletionStatus.PENDING,
        reason_code=reason_code,
        feedback=feedback,
        anonymize_only=anonymize_only,
    )


def grant_consent(
    user: User,
    *,
    consent_type: str,
    version: str,
    request: HttpRequest | None = None,
    metadata: dict | None = None,
) -> UserConsent:
    ip_address = None
    user_agent = ""
    if request is not None:
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip_address = xff.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

    consent, _created = UserConsent.objects.update_or_create(
        user=user,
        consent_type=consent_type,
        version=version,
        defaults={
            "accepted": True,
            "accepted_at": timezone.now(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {},
        },
    )
    return consent
