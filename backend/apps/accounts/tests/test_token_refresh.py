from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.tenants.models import School


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="École Refresh", slug="ecole-refresh")
        self.user = User.objects.create_user(
            email="refresh@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.user,
            role=SchoolMembership.Role.DIRECTOR,
        )

    def test_refresh_token_returns_new_access_token(self):
        login = self.client.post(
            "/api/auth/login/",
            {"email": "refresh@example.com", "password": "Password123!"},
            format="json",
            HTTP_HOST="ecole-refresh.localhost",
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("access", login.data)
        self.assertIn("refresh", login.data)

        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
