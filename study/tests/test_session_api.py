from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User


class StudySessionAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.get_or_create(slug="student", defaults={"name": "Student"})

    def setUp(self):
        reg = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "studier",
                "email": "studier@test.local",
                "password": "Str0ngPass!99",
            },
            format="json",
        )
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED, reg.data)
        payload = reg.data.get("data", reg.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {payload['access']}")

    def test_start_and_complete_session(self):
        start = self.client.post("/api/v1/study/sessions/start/", {}, format="json")
        self.assertEqual(start.status_code, status.HTTP_201_CREATED, start.data)
        body = start.data.get("data", start.data)
        session_id = str(body["id"])
        self.assertTrue(session_id)

        dup = self.client.post("/api/v1/study/sessions/start/", {}, format="json")
        self.assertEqual(dup.status_code, status.HTTP_409_CONFLICT)

        complete = self.client.post(
            f"/api/v1/study/sessions/{session_id}/complete/",
            {},
            format="json",
        )
        self.assertEqual(complete.status_code, status.HTTP_200_OK, complete.data)

    def test_cannot_access_other_user_session(self):
        start = self.client.post("/api/v1/study/sessions/start/", {}, format="json")
        session_id = str(start.data.get("data", start.data)["id"])
        other = User.objects.create_user(
            username="otherstud",
            email="otherstud@test.local",
            password="Str0ngPass!99",
            account_status="active",
        )
        self.client.force_authenticate(user=other)
        res = self.client.get(f"/api/v1/study/sessions/{session_id}/")
        self.assertIn(res.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
