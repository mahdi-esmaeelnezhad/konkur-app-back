from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from billing.models import CoachWallet, WalletTransaction
import uuid


class WalletIntegrityTests(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username="wallet_coach",
            email="wc@test.local",
            password="x",
            account_status="active",
        )
        self.wallet = CoachWallet.objects.create(
            coach=self.coach,
            balance_minor=0,
            currency="IRR",
        )

    def test_duplicate_reference_rejected(self):
        ref = uuid.uuid4()
        WalletTransaction.objects.create(
            wallet=self.wallet,
            kind="credit",
            amount_minor=1000,
            currency="IRR",
            balance_after_minor=1000,
            reference_type="payout",
            reference_id=ref,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WalletTransaction.objects.create(
                    wallet=self.wallet,
                    kind="credit",
                    amount_minor=1000,
                    currency="IRR",
                    balance_after_minor=2000,
                    reference_type="payout",
                    reference_id=ref,
                )

    def test_duplicate_idempotency_key_rejected(self):
        WalletTransaction.objects.create(
            wallet=self.wallet,
            kind="credit",
            amount_minor=500,
            currency="IRR",
            balance_after_minor=500,
            idempotency_key="credit-1",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WalletTransaction.objects.create(
                    wallet=self.wallet,
                    kind="credit",
                    amount_minor=500,
                    currency="IRR",
                    balance_after_minor=1000,
                    idempotency_key="credit-1",
                )
