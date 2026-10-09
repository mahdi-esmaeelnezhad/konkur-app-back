from django.urls import include, path
from rest_framework.routers import DefaultRouter

from education.api import views

router = DefaultRouter()
router.register(r"countries", views.CountryViewSet, basename="education-country")
router.register(
    r"education-systems",
    views.EducationSystemViewSet,
    basename="education-system",
)
router.register(r"subjects", views.SubjectViewSet, basename="education-subject")
router.register(
    r"subject-topics",
    views.SubjectTopicViewSet,
    basename="education-subject-topic",
)
router.register(r"exams", views.ExamViewSet, basename="education-exam")
router.register(r"exam-types", views.ExamTypeViewSet, basename="education-exam-type")

me_router = DefaultRouter()
me_router.register(
    r"education-profiles",
    views.UserEducationProfileViewSet,
    basename="education-me-profile",
)
me_router.register(
    r"exam-registrations",
    views.UserExamRegistrationViewSet,
    basename="education-me-exam-registration",
)

urlpatterns = [
    path("me/", include(me_router.urls)),
    path("", include(router.urls)),
]
