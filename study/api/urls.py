from django.urls import include, path
from rest_framework.routers import DefaultRouter

from study.api import views

router = DefaultRouter()
router.register(r"goals", views.GoalViewSet, basename="study-goal")
router.register(r"goal-types", views.GoalTypeViewSet, basename="study-goal-type")
router.register(r"plans", views.StudyPlanViewSet, basename="study-plan")
router.register(r"tests", views.TestDefinitionViewSet, basename="study-test")

plan_item_list = views.StudyPlanItemViewSet.as_view({"get": "list", "post": "create"})
plan_item_detail = views.StudyPlanItemViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

urlpatterns = [
    path("sessions/", views.StudySessionListCreateView.as_view(), name="study-session-list"),
    path(
        "sessions/start/",
        views.StudySessionStartView.as_view(),
        name="study-session-start",
    ),
    path(
        "sessions/<uuid:pk>/",
        views.StudySessionDetailView.as_view(),
        name="study-session-detail",
    ),
    path(
        "sessions/<uuid:pk>/pause/",
        views.StudySessionPauseView.as_view(),
        name="study-session-pause",
    ),
    path(
        "sessions/<uuid:pk>/resume/",
        views.StudySessionResumeView.as_view(),
        name="study-session-resume",
    ),
    path(
        "sessions/<uuid:pk>/complete/",
        views.StudySessionCompleteView.as_view(),
        name="study-session-complete",
    ),
    path(
        "sessions/<uuid:pk>/cancel/",
        views.StudySessionCancelView.as_view(),
        name="study-session-cancel",
    ),
    path(
        "sessions/<uuid:pk>/events/",
        views.StudySessionEventListView.as_view(),
        name="study-session-events",
    ),
    path(
        "plans/<uuid:plan_pk>/items/",
        plan_item_list,
        name="study-plan-item-list",
    ),
    path(
        "plans/<uuid:plan_pk>/items/<uuid:pk>/",
        plan_item_detail,
        name="study-plan-item-detail",
    ),
    path(
        "summaries/daily/",
        views.DailyStudySummaryListView.as_view(),
        name="study-daily-summary-list",
    ),
    path(
        "streaks/",
        views.StreakRecordListView.as_view(),
        name="study-streak-list",
    ),
    path(
        "tests/<uuid:test_pk>/attempts/",
        views.TestAttemptListCreateView.as_view(),
        name="study-test-attempt-list",
    ),
    path(
        "focus-settings/",
        views.FocusSettingsView.as_view(),
        name="study-focus-settings",
    ),
    path(
        "pomodoro-settings/",
        views.PomodoroSettingsView.as_view(),
        name="study-pomodoro-settings",
    ),
    path("", include(router.urls)),
]
