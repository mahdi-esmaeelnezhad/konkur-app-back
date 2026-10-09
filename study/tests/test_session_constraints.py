from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from study.models import StudySession


class StudySessionConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="session_user",
            email="session@konkur.test",
            password="x",
        )

    def test_rejects_negative_active_seconds(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StudySession.objects.create(
                    user=self.user,
                    status="completed",
                    source="manual",
                    started_at=timezone.now(),
                    active_seconds=-1,
                )
