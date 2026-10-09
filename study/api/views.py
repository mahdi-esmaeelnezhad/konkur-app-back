from django_filters import rest_framework as filters
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.mixins import OwnershipQuerysetMixin
from common.api.permissions import IsActiveAccount
from study.api.serializers import (
    DailyStudySummarySerializer,
    FocusSettingsSerializer,
    GoalSerializer,
    GoalTypeSerializer,
    ManualStudySessionCreateSerializer,
    PomodoroSettingsSerializer,
    StreakRecordSerializer,
    StudyPlanItemSerializer,
    StudyPlanSerializer,
    StudySessionCompleteSerializer,
    StudySessionEventSerializer,
    StudySessionNotesSerializer,
    StudySessionSerializer,
    StudySessionStartSerializer,
    TestAttemptSerializer,
    TestDefinitionSerializer,
)
from study.api.services import StudySessionService
from study.models import (
    DailyStudySummary,
    FocusSettings,
    Goal,
    GoalType,
    PomodoroSettings,
    StreakRecord,
    StudyPlan,
    StudyPlanItem,
    StudySession,
    StudySessionEvent,
    TestAttempt,
    TestDefinition,
)


class StudySessionListCreateView(OwnershipQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = StudySessionSerializer
    queryset = StudySession.objects.all().order_by("-started_at", "-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManualStudySessionCreateSerializer
        return StudySessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = ManualStudySessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = StudySessionService.log_manual_session(
            request.user,
            started_at=serializer.validated_data["started_at"],
            ended_at=serializer.validated_data["ended_at"],
            **serializer.to_session_data(),
        )
        return Response(
            StudySessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class StudySessionDetailView(OwnershipQuerysetMixin, generics.RetrieveUpdateAPIView):
    queryset = StudySession.objects.all()
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return StudySessionNotesSerializer
        return StudySessionSerializer

    def partial_update(self, request, *args, **kwargs):
        if set(request.data.keys()) - {"notes_summary"}:
            raise ValidationError("Only notes_summary can be updated.")
        return super().partial_update(request, *args, **kwargs)


class StudySessionStartView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        serializer = StudySessionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = StudySessionService.start_session(
            request.user,
            **serializer.to_session_data(),
        )
        return Response(StudySessionSerializer(session).data, status=status.HTTP_201_CREATED)


class StudySessionPauseView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request, pk):
        session = self._get_session(request.user, pk)
        session = StudySessionService.pause_session(session, request.user)
        return Response(StudySessionSerializer(session).data)

    def _get_session(self, user, pk):
        try:
            return StudySession.objects.get(pk=pk, user=user)
        except StudySession.DoesNotExist as exc:
            raise NotFound("Study session not found.") from exc


class StudySessionResumeView(StudySessionPauseView):
    def post(self, request, pk):
        session = self._get_session(request.user, pk)
        session = StudySessionService.resume_session(session, request.user)
        return Response(StudySessionSerializer(session).data)


class StudySessionCompleteView(StudySessionPauseView):
    def post(self, request, pk):
        serializer = StudySessionCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = self._get_session(request.user, pk)
        session = StudySessionService.complete_session(
            session,
            request.user,
            client_reported_seconds=serializer.validated_data.get(
                "client_reported_seconds"
            ),
        )
        return Response(StudySessionSerializer(session).data)


class StudySessionCancelView(StudySessionPauseView):
    def post(self, request, pk):
        session = self._get_session(request.user, pk)
        session = StudySessionService.cancel_session(session, request.user)
        return Response(StudySessionSerializer(session).data)


class StudySessionEventListView(OwnershipQuerysetMixin, generics.ListAPIView):
    serializer_class = StudySessionEventSerializer
    owner_field = "session__user"

    def get_queryset(self):
        session_id = self.kwargs["pk"]
        if not StudySession.objects.filter(
            pk=session_id,
            user=self.request.user,
        ).exists():
            raise NotFound("Study session not found.")
        return StudySessionEvent.objects.filter(session_id=session_id).order_by(
            "occurred_at",
            "created_at",
        )


class GoalViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    queryset = Goal.objects.all().order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GoalTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsActiveAccount]
    serializer_class = GoalTypeSerializer
    queryset = GoalType.objects.all().order_by("name")


class StudyPlanViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = StudyPlanSerializer
    queryset = StudyPlan.objects.all().order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, created_by=self.request.user)


class StudyPlanItemViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = StudyPlanItemSerializer
    owner_field = "plan__user"
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        plan_id = self.kwargs["plan_pk"]
        if not StudyPlan.objects.filter(pk=plan_id, user=self.request.user).exists():
            raise NotFound("Study plan not found.")
        return StudyPlanItem.objects.filter(plan_id=plan_id).order_by(
            "scheduled_date",
            "sort_order",
        )

    def perform_create(self, serializer):
        plan_id = self.kwargs["plan_pk"]
        try:
            plan = StudyPlan.objects.get(pk=plan_id, user=self.request.user)
        except StudyPlan.DoesNotExist as exc:
            raise NotFound("Study plan not found.") from exc
        serializer.save(plan=plan)


class DailyStudySummaryFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = DailyStudySummary
        fields = ("date_from", "date_to")


class DailyStudySummaryListView(OwnershipQuerysetMixin, generics.ListAPIView):
    serializer_class = DailyStudySummarySerializer
    queryset = DailyStudySummary.objects.all().order_by("-date")
    filterset_class = DailyStudySummaryFilter


class StreakRecordListView(OwnershipQuerysetMixin, generics.ListAPIView):
    serializer_class = StreakRecordSerializer
    queryset = StreakRecord.objects.all().order_by("streak_type")


class TestDefinitionViewSet(OwnershipQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = TestDefinitionSerializer
    owner_field = "owner"
    queryset = TestDefinition.objects.all().order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TestAttemptListCreateView(OwnershipQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = TestAttemptSerializer
    owner_field = "user"

    def get_queryset(self):
        test = self._get_test()
        return TestAttempt.objects.filter(test_definition=test).order_by("-started_at")

    def perform_create(self, serializer):
        test = self._get_test()
        serializer.save(user=self.request.user, test_definition=test)

    def _get_test(self) -> TestDefinition:
        try:
            return TestDefinition.objects.get(
                pk=self.kwargs["test_pk"],
                owner=self.request.user,
            )
        except TestDefinition.DoesNotExist as exc:
            raise NotFound("Test not found.") from exc


class FocusSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = FocusSettingsSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        obj, _created = FocusSettings.objects.get_or_create(user=self.request.user)
        return obj


class PomodoroSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsActiveAccount]
    serializer_class = PomodoroSettingsSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        obj, _created = PomodoroSettings.objects.get_or_create(user=self.request.user)
        return obj
