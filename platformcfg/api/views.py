from rest_framework import generics, viewsets
from rest_framework.filters import SearchFilter

from accounts.models import User
from common.api.permissions import IsActiveAccount, IsPlatformAdmin
from platformcfg.api.serializers import (
    AdminAuditLogSerializer,
    AdminUserSerializer,
    FeatureFlagSerializer,
)
from platformcfg.models import FeatureFlag
from safety.models import AdminAuditLog


class AdminUserSearchView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsPlatformAdmin, IsActiveAccount]
    queryset = User.objects.all().order_by("-date_joined")
    filter_backends = [SearchFilter]
    search_fields = ("username", "email", "phone")


class FeatureFlagViewSet(viewsets.ModelViewSet):
    serializer_class = FeatureFlagSerializer
    permission_classes = [IsPlatformAdmin, IsActiveAccount]
    queryset = FeatureFlag.objects.all().order_by("key")
    http_method_names = ["get", "patch", "head", "options"]
    lookup_field = "pk"


class AdminAuditLogListView(generics.ListAPIView):
    serializer_class = AdminAuditLogSerializer
    permission_classes = [IsPlatformAdmin, IsActiveAccount]
    queryset = AdminAuditLog.objects.select_related("actor").order_by("-created_at")
