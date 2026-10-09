from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User


class AuthAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.get_or_create(slug="student", defaults={"name": "Student"})

    def test_register_login_me_flow(self):
        reg = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "apiuser",
                "email": "apiuser@test.local",
                "password": "Str0ngPass!99",
            },
            format="json",
        )
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED, reg.data)
        self.assertIn("access", reg.data.get("data", reg.data))

        data = reg.data.get("data", reg.data)
        access = data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me = self.client.get("/api/v1/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)

    def test_login_rejects_bad_password(self):
        User.objects.create_user(
            username="badlogin",
            email="bad@test.local",
            password="RightPass!1",
            account_status="active",
        )
        res = self.client.post(
            "/api/v1/auth/login/",
            {"username": "badlogin", "password": "wrong"},
            format="json",
        )
        self.assertIn(res.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED))
