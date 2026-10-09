from rest_framework.response import Response


class SuccessResponseMixin:
    def success(self, data=None, status=200, meta=None):
        body = {"success": True, "data": data}
        if meta is not None:
            body["meta"] = meta
        return Response(body, status=status)


class OwnershipQuerysetMixin:
    """Force queryset to current user unless staff/platform admin."""

    owner_field = "user"

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        from common.access import is_platform_admin

        if is_platform_admin(user):
            return qs
        return qs.filter(**{self.owner_field: user})
