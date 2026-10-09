from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from org.models import ParentChildRelationship


class ParentAPITests(APITestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="parentapi",
            email="parentapi@test.local",
            password="x",
            account_status="active",
        )
        self.child = User.objects.create_user(
            username="childapi",
            email="childapi@test.local",
            password="x",
            account_status="active",
        )
        self.stranger = User.objects.create_user(
            username="strangerapi",
            email="strangerapi@test.local",
            password="x",
            account_status="active",
        )
        ParentChildRelationship.objects.create(
            parent=self.parent,
            child=self.child,
            status="active",
        )
        self.client.force_authenticate(user=self.parent)

    def test_parent_can_list_children(self):
        res = self.client.get("/api/v1/org/parent/children/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_parent_denied_unrelated_child_summary(self):
        res = self.client.get(f"/api/v1/org/parent/children/{self.stranger.id}/summary/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
