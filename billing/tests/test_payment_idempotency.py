from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from billing.models import PaymentCustomer, PaymentTransaction


class PaymentIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pay_user",
            email="pay@konkur.test",
            password="x",
        )
        self.customer = PaymentCustomer.objects.create(
            owner_kind="user",
            user=self.user,
            external_customer_id="cus_test_1",
        )

    def test_duplicate_idempotency_key_rejected(self):
        PaymentTransaction.objects.create(
            customer=self.customer,
            user=self.user,
            kind="charge",
            amount_minor=1000,
            currency="USD",
            status="succeeded",
            idempotency_key="order-1",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentTransaction.objects.create(
                    customer=self.customer,
                    user=self.user,
                    kind="charge",
                    amount_minor=1000,
                    currency="USD",
                    status="succeeded",
                    idempotency_key="order-1",
                )
