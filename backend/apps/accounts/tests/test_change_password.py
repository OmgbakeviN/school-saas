from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.tenants.models import School


class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Password School",
            slug="password-school",
        )
        self.user = User.objects.create_user(
            email="teacher-password@example.com",
            password="OldPassword123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.user,
            role=SchoolMembership.Role.TEACHER,
        )

        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "teacher-password@example.com",
                "password": "OldPassword123!",
            },
            format="json",
            HTTP_HOST="password-school.localhost",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

    def test_authenticated_member_can_change_own_password(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
            format="json",
            HTTP_HOST="password-school.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123!"))
