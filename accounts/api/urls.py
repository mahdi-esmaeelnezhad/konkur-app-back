from django.urls import path

from accounts.api import views

auth_urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("password/change/", views.PasswordChangeView.as_view(), name="password-change"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]

me_urlpatterns = [
    path("", views.MeView.as_view(), name="me"),
    path("profile/", views.MeProfileView.as_view(), name="me-profile"),
    path("settings/", views.MeSettingsView.as_view(), name="me-settings"),
    path("preferences/", views.MePreferencesView.as_view(), name="me-preferences"),
    path("privacy/", views.MePrivacyView.as_view(), name="me-privacy"),
    path("roles/", views.MeRolesView.as_view(), name="me-roles"),
    path("devices/", views.MeDeviceListCreateView.as_view(), name="me-devices"),
    path(
        "devices/<uuid:device_id>/",
        views.MeDeviceDestroyView.as_view(),
        name="me-device-detail",
    ),
    path("blocks/", views.MeBlockListCreateView.as_view(), name="me-blocks"),
    path(
        "blocks/<uuid:block_id>/",
        views.MeBlockDestroyView.as_view(),
        name="me-block-detail",
    ),
    path(
        "deletion-request/",
        views.MeDeletionRequestView.as_view(),
        name="me-deletion-request",
    ),
    path("consents/", views.MeConsentListView.as_view(), name="me-consents"),
]
