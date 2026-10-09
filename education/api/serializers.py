from rest_framework import serializers

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


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            "id",
            "iso_code",
            "name",
            "native_name",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class EducationSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationSystem
        fields = (
            "id",
            "country",
            "code",
            "name",
            "description",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = (
            "id",
            "code",
            "name",
            "description",
            "education_system",
            "exam",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class SubjectTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectTopic
        fields = (
            "id",
            "subject",
            "parent",
            "code",
            "name",
            "description",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamType
        fields = (
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            "id",
            "exam_type",
            "country",
            "education_system",
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class UserEducationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEducationProfile
        fields = (
            "id",
            "user",
            "institution",
            "program",
            "major",
            "level",
            "grade",
            "status",
            "is_primary",
            "started_on",
            "ended_on",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")


class UserExamRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExamRegistration
        fields = (
            "id",
            "user",
            "exam",
            "session",
            "status",
            "registered_at",
            "external_registration_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "registered_at", "created_at", "updated_at")
