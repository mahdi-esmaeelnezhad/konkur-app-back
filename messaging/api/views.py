from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.access import conversation_messages_for_participant
from common.api.mixins import OwnershipQuerysetMixin
from common.api.permissions import IsActiveAccount
from messaging.api import services
from messaging.api.serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    NotificationSerializer,
    UserNotificationSettingSerializer,
)
from messaging.models import Conversation, ConversationParticipant, Message, Notification, UserNotificationSetting


class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        conversation_ids = ConversationParticipant.objects.filter(
            user=self.request.user,
            left_at__isnull=True,
        ).values_list("conversation_id", flat=True)
        return Conversation.objects.filter(id__in=conversation_ids).order_by("-last_message_at", "-created_at")

    def create(self, request, *args, **kwargs):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        other_user_id = serializer.validated_data["user_id"]
        if str(other_user_id) == str(request.user.id):
            raise ValidationError("Cannot create a conversation with yourself.")
        try:
            conversation, created = services.get_or_create_direct_conversation(
                request.user,
                other_user_id,
            )
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConversationMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MessageCreateSerializer
        return MessageSerializer

    def _conversation_id(self):
        return self.kwargs["conversation_id"]

    def _ensure_participant(self):
        if not services.user_participates_in_conversation(self.request.user, self._conversation_id()):
            raise PermissionDenied("You are not a participant in this conversation.")

    def get_queryset(self):
        self._ensure_participant()
        return conversation_messages_for_participant(
            self.request.user,
            self._conversation_id(),
        ).select_related("sender").order_by("created_at")

    def list(self, request, *args, **kwargs):
        if not services.user_participates_in_conversation(request.user, self._conversation_id()):
            raise PermissionDenied()
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        self._ensure_participant()
        conversation_id = self._conversation_id()
        message = serializer.save(
            conversation_id=conversation_id,
            sender=self.request.user,
        )
        Conversation.objects.filter(pk=conversation_id).update(
            last_message_at=timezone.now(),
        )
        return message


class ConversationMarkReadView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def post(self, request, conversation_id):
        if not services.user_participates_in_conversation(request.user, conversation_id):
            raise PermissionDenied()
        services.mark_conversation_read(request.user, conversation_id)
        return Response({"read": True})


class NotificationListView(OwnershipQuerysetMixin, generics.ListAPIView):
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated, IsActiveAccount]


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def post(self, request, pk):
        notification = Notification.objects.filter(pk=pk, user=request.user).first()
        if notification is None:
            raise NotFound()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def post(self, request):
        now = timezone.now()
        updated = Notification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=now,
            updated_at=now,
        )
        return Response({"updated": updated})


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({"unread_count": count})


class NotificationPreferencesView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationSettingSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]

    def get_object(self):
        obj, _created = UserNotificationSetting.objects.get_or_create(user=self.request.user)
        return obj
