from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platformcfg.api import views

router = DefaultRouter()
router.register(r"feature-flags", views.FeatureFlagViewSet, basename="admin-feature-flag")

urlpatterns = [
    path("users/", views.AdminUserSearchView.as_view(), name="admin-user-search"),
    path("audit-logs/", views.AdminAuditLogListView.as_view(), name="admin-audit-log-list"),
    path("", include(router.urls)),
]
