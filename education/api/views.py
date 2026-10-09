from django_filters import rest_framework as filters
from rest_framework import viewsets

from common.api.mixins import OwnershipQuerysetMixin
from common.api.permissions import IsActiveAccount
from education.api.serializers import (
    CountrySerializer,
    EducationSystemSerializer,
    ExamSerializer,
    ExamTypeSerializer,
    SubjectSerializer,
    SubjectTopicSerializer,
    UserEducationProfileSerializer,
    UserExamRegistrationSerializer,
)
from education.models import (
    Country,
    EducationSystem,
    Exam,
    ExamType,
    Subject,
    SubjectTopic,
    UserEducationProfile,
    UserExamRegistration,
)


class ActiveCatalogFilter(filters.FilterSet):
    is_active = filters.BooleanFilter(field_name="is_active")


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = CountrySerializer
    queryset = Country.objects.filter(is_active=True).order_by("name")
    filterset_class = ActiveCatalogFilter


class EducationSystemViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = EducationSystemSerializer
    queryset = EducationSystem.objects.filter(is_active=True).order_by(
        "sort_order",
        "name",
    )
    filterset_fields = ("country",)
    filterset_class = ActiveCatalogFilter


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = SubjectSerializer
    queryset = Subject.objects.filter(is_active=True).order_by("sort_order", "name")
    filterset_fields = ("education_system", "exam")
    filterset_class = ActiveCatalogFilter


class SubjectTopicViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = SubjectTopicSerializer
    queryset = SubjectTopic.objects.filter(is_active=True).order_by(
        "sort_order",
        "name",
    )
    filterset_fields = ("subject", "parent")
    filterset_class = ActiveCatalogFilter


class ExamTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = ExamTypeSerializer
    queryset = ExamType.objects.filter(is_active=True).order_by("name")
    filterset_class = ActiveCatalogFilter


class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = ExamSerializer
    queryset = Exam.objects.filter(is_active=True).order_by("name")
    filterset_fields = ("exam_type", "country", "education_system")
    filterset_class = ActiveCatalogFilter


class UserEducationProfileViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = UserEducationProfileSerializer
    queryset = UserEducationProfile.objects.all().order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserExamRegistrationViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = UserExamRegistrationSerializer
    queryset = UserExamRegistration.objects.all().order_by("-registered_at")
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
