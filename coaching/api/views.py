from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.access import coach_can_access_student, coach_notes_queryset_for_user
from common.api.permissions import CanAccessCoachStudent, IsActiveAccount
from coaching.api import services
from coaching.api.serializers import (
    CoachAssignmentSerializer,
    CoachNoteSerializer,
    CoachProfileMeSerializer,
    CoachProfilePublicSerializer,
    CoachReviewSerializer,
    CoachStudentRelationshipSerializer,
    CoachStudentRequestCreateSerializer,
    CoachStudentRequestSerializer,
)
from coaching.models import (
    CoachAssignment,
    CoachProfile,
    CoachReview,
    CoachStudentRelationship,
    CoachStudentRequest,
    CoachStudentRequestStatus,
)


class CoachProfileFilter(filters.FilterSet):
    specialty = filters.CharFilter(method="filter_specialty")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = CoachProfile
        fields = []

    def filter_specialty(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(specialties__slug__iexact=value) | Q(specialties__name__icontains=value)
        ).distinct()

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(headline__icontains=value)
            | Q(bio__icontains=value)
            | Q(specialties__name__icontains=value)
            | Q(specialties__slug__icontains=value)
        ).distinct()


class CoachProfilePublicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CoachProfilePublicSerializer
    queryset = CoachProfile.objects.select_related("user").prefetch_related("specialties")
    filterset_class = CoachProfileFilter
    permission_classes = [AllowAny]
    lookup_field = "pk"


class MyCoachProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CoachProfileMeSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_object(self):
        return services.get_or_create_coach_profile(self.request.user)


class CoachStudentListView(generics.ListAPIView):
    serializer_class = CoachStudentRelationshipSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_queryset(self):
        profile = services.get_or_create_coach_profile(self.request.user)
        return (
            CoachStudentRelationship.objects.filter(coach=profile)
            .select_related("student")
            .order_by("-created_at")
        )


class CoachStudentProgressView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanAccessCoachStudent]

    def get(self, request, student_id):
        if not coach_can_access_student(request.user, student_id):
            raise PermissionDenied("You do not have access to this student.")
        return Response(services.build_student_progress_summary(student_id))


class CoachNoteListCreateView(generics.ListCreateAPIView):
    serializer_class = CoachNoteSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_queryset(self):
        return coach_notes_queryset_for_user(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        profile = services.get_or_create_coach_profile(self.request.user)
        serializer.save(coach=profile)


class CoachAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = CoachAssignmentSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        profile = CoachProfile.objects.filter(user=self.request.user).first()
        if profile is None:
            return CoachAssignment.objects.none()
        return CoachAssignment.objects.filter(coach=profile).order_by("-created_at")

    def perform_create(self, serializer):
        profile = services.get_or_create_coach_profile(self.request.user)
        serializer.save(coach=profile)


class CoachStudentRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CoachStudentRequestCreateSerializer
        return CoachStudentRequestSerializer

    def get_queryset(self):
        user = self.request.user
        profile = CoachProfile.objects.filter(user=user).first()
        if profile is not None:
            return (
                CoachStudentRequest.objects.filter(coach=profile)
                .select_related("coach__user", "student")
                .order_by("-created_at")
            )
        return (
            CoachStudentRequest.objects.filter(student=user)
            .select_related("coach__user", "student")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(student=self.request.user, status=CoachStudentRequestStatus.PENDING)


class CoachStudentRequestAcceptView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def post(self, request, pk):
        request_obj = CoachStudentRequest.objects.select_related("coach__user").filter(pk=pk).first()
        if request_obj is None:
            raise NotFound()
        try:
            relationship = services.accept_coach_student_request(request_obj, request.user)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            CoachStudentRelationshipSerializer(relationship).data,
            status=status.HTTP_200_OK,
        )


class CoachStudentRequestDeclineView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def post(self, request, pk):
        request_obj = CoachStudentRequest.objects.select_related("coach__user").filter(pk=pk).first()
        if request_obj is None:
            raise NotFound()
        try:
            services.decline_coach_student_request(request_obj, request.user)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response({"status": CoachStudentRequestStatus.DECLINED})


class CoachReviewListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_serializer_class(self):
        return CoachReviewSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        qs = CoachReview.objects.filter(is_public=True).select_related("reviewer", "coach")
        coach_id = self.request.query_params.get("coach")
        if coach_id:
            qs = qs.filter(coach_id=coach_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
