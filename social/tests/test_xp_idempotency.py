from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from social.models import XpTransaction


class XpIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="xp_user",
            email="xp@konkur.test",
            password="x",
        )

    def test_duplicate_idempotency_key_rejected(self):
        XpTransaction.objects.create(
            user=self.user,
            amount=50,
            source_type="achievement",
            idempotency_key="first_session:v1",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                XpTransaction.objects.create(
                    user=self.user,
                    amount=50,
                    source_type="achievement",
                    idempotency_key="first_session:v1",
                )
