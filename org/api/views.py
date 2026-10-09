from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.access import org_admin_can_access, org_member_can, parent_can_view_child, teacher_can_access_class
from common.api.permissions import CanAccessChild, CanAccessOrganization, IsActiveAccount
from org.api import services
from org.api.serializers import (
    OrganizationMembershipSerializer,
    OrganizationSerializer,
    ParentChildRelationshipSerializer,
    ParentLinkInviteSerializer,
    SchoolSerializer,
    TeacherClassAssignmentSerializer,
)
from org.models import (
    Organization,
    OrganizationMembership,
    OrganizationMembershipStatus,
    ParentChildRelationship,
    ParentChildRelationshipStatus,
    School,
    SchoolMembership,
    TeacherClassAssignment,
    TeacherProfile,
)


class ParentChildrenListView(generics.ListAPIView):
    serializer_class = ParentChildRelationshipSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_queryset(self):
        return (
            ParentChildRelationship.objects.filter(
                parent=self.request.user,
                status=ParentChildRelationshipStatus.ACTIVE,
            )
            .select_related("child")
            .order_by("-created_at")
        )


class ParentChildSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount, CanAccessChild]

    def get(self, request, child_id):
        if not parent_can_view_child(request.user.id, child_id):
            return Response(
                {"detail": "You do not have permission to view this child."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(services.build_child_summary(child_id))


class ParentLinkRequestCreateView(generics.CreateAPIView):
    serializer_class = ParentLinkInviteSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        child_id = serializer.validated_data["child_id"]
        if str(request.user.id) == str(child_id):
            raise ValidationError("Cannot link to yourself.")
        relationship = services.create_parent_link_invite(request.user, child_id)
        return Response(
            ParentChildRelationshipSerializer(relationship).data,
            status=status.HTTP_201_CREATED,
        )


class ParentLinkRequestAcceptView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def post(self, request, pk):
        relationship = ParentChildRelationship.objects.filter(pk=pk).first()
        if relationship is None:
            raise NotFound()
        try:
            relationship = services.accept_parent_link_invite(relationship, request.user)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ParentChildRelationshipSerializer(relationship).data)


class OrganizationListView(generics.ListAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_queryset(self):
        org_ids = OrganizationMembership.objects.filter(
            user=self.request.user,
            status=OrganizationMembershipStatus.ACTIVE,
        ).values_list("organization_id", flat=True)
        return Organization.objects.filter(id__in=org_ids).order_by("name")


class OrganizationDetailView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]
    queryset = Organization.objects.all()
    lookup_field = "pk"

    def get_object(self):
        obj = super().get_object()
        if not org_member_can(self.request.user, obj.id):
            raise PermissionDenied("You are not a member of this organization.")
        return obj


class OrganizationMemberListView(generics.ListAPIView):
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount, CanAccessOrganization]

    def get_queryset(self):
        organization_id = self.kwargs["organization_id"]
        if not org_admin_can_access(self.request.user, organization_id):
            raise PermissionDenied("Organization admin access required.")
        return (
            OrganizationMembership.objects.filter(organization_id=organization_id)
            .select_related("user")
            .order_by("role", "-created_at")
        )


class SchoolListView(generics.ListAPIView):
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_queryset(self):
        user = self.request.user
        org_ids = OrganizationMembership.objects.filter(
            user=user,
            status=OrganizationMembershipStatus.ACTIVE,
        ).values_list("organization_id", flat=True)
        school_ids = SchoolMembership.objects.filter(
            user=user,
            left_at__isnull=True,
        ).values_list("school_id", flat=True)
        return School.objects.filter(
            Q(organization_id__in=org_ids) | Q(id__in=school_ids)
        ).distinct().order_by("name")


class TeacherClassListView(generics.ListAPIView):
    serializer_class = TeacherClassAssignmentSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_queryset(self):
        profile_ids = TeacherProfile.objects.filter(user=self.request.user).values_list("id", flat=True)
        return TeacherClassAssignment.objects.filter(teacher_id__in=profile_ids).order_by(
            "-academic_year", "class_name"
        )


class TeacherClassDetailView(generics.RetrieveAPIView):
    serializer_class = TeacherClassAssignmentSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]
    queryset = TeacherClassAssignment.objects.all()
    lookup_field = "pk"

    def get_object(self):
        obj = super().get_object()
        if not teacher_can_access_class(self.request.user, obj.id):
            raise PermissionDenied("You do not have access to this class.")
        return obj
