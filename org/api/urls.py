from django.urls import path

from org.api import views

urlpatterns = [
    path("parent/children/", views.ParentChildrenListView.as_view(), name="parent-children"),
    path(
        "parent/children/<uuid:child_id>/summary/",
        views.ParentChildSummaryView.as_view(),
        name="parent-child-summary",
    ),
    path(
        "parent/link-requests/",
        views.ParentLinkRequestCreateView.as_view(),
        name="parent-link-request-create",
    ),
    path(
        "parent/link-requests/<uuid:pk>/accept/",
        views.ParentLinkRequestAcceptView.as_view(),
        name="parent-link-request-accept",
    ),
    path("organizations/", views.OrganizationListView.as_view(), name="organization-list"),
    path(
        "organizations/<uuid:pk>/",
        views.OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
    path(
        "organizations/<uuid:organization_id>/members/",
        views.OrganizationMemberListView.as_view(),
        name="organization-members",
    ),
    path("schools/", views.SchoolListView.as_view(), name="school-list"),
    path("teacher/classes/", views.TeacherClassListView.as_view(), name="teacher-class-list"),
    path(
        "teacher/classes/<uuid:pk>/",
        views.TeacherClassDetailView.as_view(),
        name="teacher-class-detail",
    ),
]
