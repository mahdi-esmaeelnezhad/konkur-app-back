from django.urls import include, path
from rest_framework.routers import DefaultRouter

from coaching.api import views

router = DefaultRouter()
router.register(r"coaches", views.CoachProfilePublicViewSet, basename="coach-profile")
router.register(r"assignments", views.CoachAssignmentViewSet, basename="coach-assignment")

urlpatterns = [
    path("me/coach-profile/", views.MyCoachProfileView.as_view(), name="coach-me-profile"),
    path("students/", views.CoachStudentListView.as_view(), name="coach-student-list"),
    path(
        "students/<uuid:student_id>/",
        views.CoachStudentProgressView.as_view(),
        name="coach-student-progress",
    ),
    path("notes/", views.CoachNoteListCreateView.as_view(), name="coach-note-list"),
    path(
        "requests/",
        views.CoachStudentRequestListCreateView.as_view(),
        name="coach-student-request-list",
    ),
    path(
        "requests/<uuid:pk>/accept/",
        views.CoachStudentRequestAcceptView.as_view(),
        name="coach-student-request-accept",
    ),
    path(
        "requests/<uuid:pk>/decline/",
        views.CoachStudentRequestDeclineView.as_view(),
        name="coach-student-request-decline",
    ),
    path("reviews/", views.CoachReviewListCreateView.as_view(), name="coach-review-list"),
    path("", include(router.urls)),
]
