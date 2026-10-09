from rest_framework import serializers

from accounts.api.public_serializers import UserPublicSerializer
from coaching.models import (
    CoachAssignment,
    CoachNote,
    CoachProfile,
    CoachReview,
    CoachSpecialty,
    CoachStudentRelationship,
    CoachStudentRequest,
)


class CoachSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachSpecialty
        fields = ("id", "slug", "name", "description")
        read_only_fields = fields


class CoachProfilePublicSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    specialties = CoachSpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = CoachProfile
        fields = (
            "id",
            "user",
            "headline",
            "bio",
            "education_summary",
            "years_experience",
            "is_accepting_students",
            "is_verified",
            "average_rating",
            "review_count",
            "specialties",
            "created_at",
        )
        read_only_fields = fields


class CoachProfileMeSerializer(serializers.ModelSerializer):
    specialty_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CoachSpecialty.objects.all(),
        source="specialties",
        required=False,
    )

    class Meta:
        model = CoachProfile
        fields = (
            "id",
            "headline",
            "bio",
            "education_summary",
            "years_experience",
            "student_capacity",
            "is_accepting_students",
            "specialty_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class CoachStudentRelationshipSerializer(serializers.ModelSerializer):
    student = UserPublicSerializer(read_only=True)

    class Meta:
        model = CoachStudentRelationship
        fields = (
            "id",
            "student",
            "status",
            "started_at",
            "ended_at",
            "created_at",
        )
        read_only_fields = fields


class CoachNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachNote
        fields = ("id", "student", "body", "is_pinned", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_student(self, value):
        from common.access import coach_can_access_student

        request = self.context["request"]
        if not coach_can_access_student(request.user, value.id):
            raise serializers.ValidationError(
                "No active coaching relationship with this student."
            )
        return value


class CoachAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachAssignment
        fields = (
            "id",
            "student",
            "title",
            "instructions",
            "due_at",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_student(self, value):
        from common.access import coach_can_access_student

        request = self.context["request"]
        if not coach_can_access_student(request.user, value.id):
            raise serializers.ValidationError(
                "No active coaching relationship with this student."
            )
        return value


class CoachStudentRequestSerializer(serializers.ModelSerializer):
    coach = CoachProfilePublicSerializer(read_only=True)
    student = UserPublicSerializer(read_only=True)

    class Meta:
        model = CoachStudentRequest
        fields = ("id", "coach", "student", "message", "status", "created_at", "updated_at")
        read_only_fields = fields


class CoachStudentRequestCreateSerializer(serializers.ModelSerializer):
    coach_id = serializers.PrimaryKeyRelatedField(
        queryset=CoachProfile.objects.all(),
        source="coach",
    )

    class Meta:
        model = CoachStudentRequest
        fields = ("coach_id", "message")


class CoachReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachReview
        fields = (
            "id",
            "coach",
            "reviewer",
            "relationship",
            "rating",
            "comment",
            "is_public",
            "created_at",
        )
        read_only_fields = ("id", "reviewer", "created_at")

    def validate(self, attrs):
        from coaching.models import CoachStudentRelationship

        request = self.context["request"]
        coach = attrs.get("coach") or getattr(self.instance, "coach", None)
        if coach is None:
            raise serializers.ValidationError({"coach": "This field is required."})

        relationship = CoachStudentRelationship.objects.filter(
            coach=coach,
            student=request.user,
            status="active",
        ).first()
        if relationship is None:
            raise serializers.ValidationError(
                "An active coaching relationship is required to leave a review."
            )
        attrs["relationship"] = relationship
        attrs["reviewer"] = request.user
        return attrs
