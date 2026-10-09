from rest_framework import serializers

from accounts.api.public_serializers import UserPublicSerializer
from org.models import (
    Organization,
    OrganizationMembership,
    ParentChildRelationship,
    School,
    TeacherClassAssignment,
)


class ParentChildRelationshipSerializer(serializers.ModelSerializer):
    child = UserPublicSerializer(read_only=True)

    class Meta:
        model = ParentChildRelationship
        fields = (
            "id",
            "child",
            "status",
            "invited_at",
            "accepted_at",
            "created_at",
        )
        read_only_fields = fields


class ParentLinkInviteSerializer(serializers.Serializer):
    child_id = serializers.UUIDField()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
            "kind",
            "status",
            "country_code",
            "timezone",
            "contact_email",
            "created_at",
        )
        read_only_fields = fields


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = (
            "id",
            "user",
            "role",
            "status",
            "joined_at",
            "created_at",
        )
        read_only_fields = fields


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = (
            "id",
            "organization",
            "name",
            "slug",
            "status",
            "address",
            "timezone",
            "created_at",
        )
        read_only_fields = fields


class TeacherClassAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClassAssignment
        fields = (
            "id",
            "school",
            "class_name",
            "section",
            "subject_name",
            "academic_year",
            "grade_level",
            "created_at",
        )
        read_only_fields = fields
