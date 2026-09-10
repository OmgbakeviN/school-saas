from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import User, SchoolMembership
from apps.tenants.models import School


class TenantIsolationTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name="École A",
            slug="ecole-a",
        )
        self.school_b = School.objects.create(
            name="École B",
            slug="ecole-b",
        )

        self.user_a = User.objects.create_user(
            email="a@example.com",
            password="Password123!",
            first_name="Alice",
        )

        SchoolMembership.objects.create(
            user=self.user_a,
            school=self.school_a,
            role=SchoolMembership.Role.DIRECTOR,
        )

    def test_user_cannot_login_to_other_tenant(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "a@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="ecole-b.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_authenticated_user_cannot_read_other_tenant_settings(self):
        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "a@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(
            login.status_code,
            200,
            msg=f"Login response: {getattr(login, 'data', None)}",
        )
        self.assertIn("access", login.data)

        token = login.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

        response = self.client.get(
            "/api/tenant/settings/",
            HTTP_HOST="ecole-b.localhost",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_debug_tenant_header_still_works_for_local_vite(self):
        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "a@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_X_TENANT_SLUG="ecole-a",
        )

        self.assertEqual(
            login.status_code,
            200,
            msg=f"Login response: {getattr(login, 'data', None)}",
        )
        self.assertIn("access", login.data)
