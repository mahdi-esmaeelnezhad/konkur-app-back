from rest_framework.permissions import BasePermission, SAFE_METHODS

from common.access import (
    coach_can_access_student,
    is_platform_admin,
    org_admin_can_access,
    parent_can_view_child,
    user_has_active_role,
)


class IsActiveAccount(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "account_status", "active") in {"active", "pending"}


class HasActiveRole(BasePermission):
    role_slug = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        slug = getattr(view, "required_role", self.role_slug)
        if not slug:
            return True
        return user_has_active_role(request.user, slug) or is_platform_admin(request.user)


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_platform_admin(request.user))


class IsOwnerOrReadOnly(BasePermission):
    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, self.owner_field, None)
        if owner is None and hasattr(obj, "author"):
            owner = obj.author
        return owner == request.user


class CanAccessChild(BasePermission):
    def has_permission(self, request, view):
        child_id = view.kwargs.get("child_id") or request.query_params.get("child_id")
        if not child_id:
            return True
        return parent_can_view_child(request.user.id, child_id)


class CanAccessCoachStudent(BasePermission):
    def has_permission(self, request, view):
        student_id = view.kwargs.get("student_id") or request.query_params.get("student_id")
        if not student_id:
            return True
        return coach_can_access_student(request.user, student_id)


class CanAccessOrganization(BasePermission):
    def has_permission(self, request, view):
        org_id = view.kwargs.get("organization_id") or view.kwargs.get("pk")
        if not org_id:
            return True
        return org_admin_can_access(request.user, org_id)
