from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from common.access import user_is_blocked
from messaging.models import (
    Conversation,
    ConversationKind,
    ConversationParticipant,
    Message,
    MessageReceipt,
)


@transaction.atomic
def get_or_create_direct_conversation(creator, other_user_id):
    if user_is_blocked(creator.id, other_user_id):
        raise PermissionError("Cannot start a conversation with this user.")

    my_conversation_ids = ConversationParticipant.objects.filter(
        user=creator,
        left_at__isnull=True,
    ).values_list("conversation_id", flat=True)

    for conversation_id in my_conversation_ids:
        participant_ids = set(
            ConversationParticipant.objects.filter(
                conversation_id=conversation_id,
                left_at__isnull=True,
            ).values_list("user_id", flat=True)
        )
        if participant_ids == {creator.id, other_user_id}:
            conversation = Conversation.objects.filter(
                pk=conversation_id,
                kind=ConversationKind.DIRECT,
            ).first()
            if conversation is not None:
                return conversation, False

    conversation = Conversation.objects.create(
        kind=ConversationKind.DIRECT,
        created_by=creator,
    )
    ConversationParticipant.objects.create(conversation=conversation, user=creator)
    ConversationParticipant.objects.create(conversation=conversation, user_id=other_user_id)
    return conversation, True


def user_participates_in_conversation(user, conversation_id) -> bool:
    return ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user=user,
        left_at__isnull=True,
    ).exists()


def mark_conversation_read(user, conversation_id) -> None:
    now = timezone.now()
    ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user=user,
        left_at__isnull=True,
    ).update(last_read_at=now, updated_at=now)

    message_ids = Message.objects.filter(conversation_id=conversation_id).values_list("id", flat=True)
    for message_id in message_ids:
        MessageReceipt.objects.update_or_create(
            message_id=message_id,
            user=user,
            defaults={"read_at": now},
        )
