from datetime import date

from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.tenants.models import School
from apps.academics.models import AcademicYear, Cycle, Level, Section


class AcademicStructureTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name="École A",
            slug="ecole-a",
            language_mode=School.LanguageMode.FRENCH,
            education_level=School.EducationLevel.PRIMARY_SECONDARY,
        )
        self.school_b = School.objects.create(
            name="École B",
            slug="ecole-b",
        )

        self.user = User.objects.create_user(
            email="director@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school_a,
            user=self.user,
            role=SchoolMembership.Role.DIRECTOR,
        )

        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "director@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )
        self.assertEqual(login.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

    def test_bootstrap_creates_suggested_structure_only_in_current_school(self):
        response = self.client.post(
            "/api/academics/bootstrap/",
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreater(Section.objects.filter(school=self.school_a).count(), 0)
        self.assertGreater(Cycle.objects.filter(school=self.school_a).count(), 0)
        self.assertGreater(Level.objects.filter(school=self.school_a).count(), 0)
        self.assertEqual(Section.objects.filter(school=self.school_b).count(), 0)

    def test_cannot_create_level_using_cycle_from_another_school(self):
        foreign_section = Section.objects.create(
            school=self.school_b,
            name="Foreign",
            code="foreign",
        )
        foreign_cycle = Cycle.objects.create(
            school=self.school_b,
            section=foreign_section,
            name="Foreign cycle",
            code="foreign-cycle",
        )

        response = self.client.post(
            "/api/academics/levels/",
            {
                "cycle": foreign_cycle.id,
                "name": "3e",
                "code": "3e",
                "order": 1,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_activating_new_year_deactivates_previous_one(self):
        first = AcademicYear.objects.create(
            school=self.school_a,
            name="2025/2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
        )

        response = self.client.post(
            "/api/academics/years/",
            {
                "name": "2026/2027",
                "start_date": "2026-09-01",
                "end_date": "2027-06-30",
                "period_system": "TRIMESTER",
                "is_active": True,
                "is_closed": False,
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 201)
        first.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(
            AcademicYear.objects.get(
                school=self.school_a,
                name="2026/2027",
            ).is_active
        )
