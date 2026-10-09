import json

from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import PaymentWebhookEvent, PaymentWebhookProcessingStatus, SubscriptionPlan, UserSubscription
from billing.api.serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from common.api.mixins import OwnershipQuerysetMixin
from common.api.permissions import IsActiveAccount


class SubscriptionPlanListView(generics.ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by("sort_order", "name")


class MySubscriptionListView(OwnershipQuerysetMixin, generics.ListAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsActiveAccount]
    queryset = UserSubscription.objects.select_related("plan").order_by("-created_at")


class StripeWebhookView(APIView):
    """
    Stripe webhook stub.

    Production deployments MUST verify the ``Stripe-Signature`` header before
    trusting event payloads or marking payments succeeded. This endpoint only
    records events with ``processing_status=received`` and does not update
    payment or subscription state.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get("Stripe-Signature")
        if not signature:
            return Response(
                {
                    "detail": (
                        "Missing Stripe-Signature header. "
                        "Configure webhook signing secret verification before processing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON body."}, status=status.HTTP_400_BAD_REQUEST)

        external_event_id = payload.get("id")
        if not external_event_id:
            return Response({"detail": "Missing event id."}, status=status.HTTP_400_BAD_REQUEST)

        event_type = payload.get("type", "unknown")

        try:
            with transaction.atomic():
                PaymentWebhookEvent.objects.create(
                    provider="stripe",
                    external_event_id=external_event_id,
                    event_type=event_type,
                    payload=payload,
                    processing_status=PaymentWebhookProcessingStatus.RECEIVED,
                )
        except IntegrityError:
            return Response(
                {"received": True, "duplicate": True},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"received": True, "processing_status": PaymentWebhookProcessingStatus.RECEIVED},
            status=status.HTTP_201_CREATED,
        )
