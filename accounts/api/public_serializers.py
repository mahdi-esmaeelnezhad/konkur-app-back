from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from accounts.models import User


class UserPublicSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "display_name", "avatar")
        read_only_fields = fields

    def _profile(self, obj: User):
        try:
            return obj.profile
        except ObjectDoesNotExist:
            return None

    def get_display_name(self, obj: User) -> str:
        profile = self._profile(obj)
        if profile and profile.display_name:
            return profile.display_name
        return obj.username

    def get_avatar(self, obj: User) -> str:
        profile = self._profile(obj)
        return profile.avatar_url if profile else ""
