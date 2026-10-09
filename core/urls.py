from django.urls import include, path

from accounts.api.urls import auth_urlpatterns, me_urlpatterns

from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("v1/auth/", include((auth_urlpatterns, "auth"))),
    path("v1/me/", include((me_urlpatterns, "me"))),
    path("v1/study/", include("study.api.urls")),
    path("v1/social/", include("social.api.urls")),
    path("v1/education/", include("education.api.urls")),
    path("v1/coaching/", include("coaching.api.urls")),
    path("v1/org/", include("org.api.urls")),
    path("v1/messaging/", include("messaging.api.urls")),
    path("v1/admin/", include("platformcfg.api.urls")),
    path("v1/billing/", include("billing.api.urls")),
]
