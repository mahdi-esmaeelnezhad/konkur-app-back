from django.db import IntegrityError, transaction
from django.test import TestCase

from billing.models import PaymentWebhookEvent


class WebhookIdempotencyTests(TestCase):
    def test_duplicate_external_event_id_rejected(self):
        PaymentWebhookEvent.objects.create(
            provider="stripe",
            external_event_id="evt_123",
            event_type="payment_intent.succeeded",
            payload={"ok": True},
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentWebhookEvent.objects.create(
                    provider="stripe",
                    external_event_id="evt_123",
                    event_type="payment_intent.succeeded",
                    payload={"ok": True},
                )
