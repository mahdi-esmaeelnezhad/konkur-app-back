from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Role, User, UserRole


class MultiRoleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="multi_role",
            email="multi@konkur.test",
            password="x",
        )
        self.student = Role.objects.create(slug="student", name="Student")
        self.coach = Role.objects.create(slug="coach", name="Coach")

    def test_user_can_hold_multiple_roles(self):
        UserRole.objects.create(user=self.user, role=self.student, is_primary=True)
        UserRole.objects.create(user=self.user, role=self.coach, is_primary=False)
        self.assertEqual(self.user.user_roles.count(), 2)

    def test_duplicate_user_role_rejected(self):
        UserRole.objects.create(user=self.user, role=self.student, is_primary=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserRole.objects.create(user=self.user, role=self.student)

    def test_only_one_primary_active_role(self):
        UserRole.objects.create(user=self.user, role=self.student, is_primary=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserRole.objects.create(user=self.user, role=self.coach, is_primary=True)
