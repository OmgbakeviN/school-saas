from datetime import date
from decimal import Decimal

from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import (
    AcademicPolicy,
    AcademicYear,
    Cycle,
    Level,
    Section,
    Subject,
)
from apps.tenants.models import School


class CurriculumRulesTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="École A",
            slug="ecole-a",
            language_mode=School.LanguageMode.FRENCH,
        )
        self.other_school = School.objects.create(
            name="École B",
            slug="ecole-b",
        )

        self.user = User.objects.create_user(
            email="director-curriculum@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolMembership.Role.DIRECTOR,
        )

        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "director-curriculum@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )
        self.assertEqual(login.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026/2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            period_system=AcademicYear.PeriodSystem.TRIMESTER,
            is_active=True,
        )

        self.section = Section.objects.create(
            school=self.school,
            name="Section francophone",
            code="fr",
        )
        self.cycle = Cycle.objects.create(
            school=self.school,
            section=self.section,
            name="Secondaire",
            code="fr-secondaire",
        )
        self.level = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="3e",
            code="3e",
        )

    def test_policy_can_use_school_specific_promotion_threshold(self):
        response = self.client.patch(
            "/api/academics/policy/",
            {
                "default_max_score": "20.00",
                "default_promotion_threshold": "12.00",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 200)
        policy = AcademicPolicy.objects.get(school=self.school)
        self.assertEqual(
            policy.default_promotion_threshold,
            Decimal("12.00"),
        )

    def test_level_inherits_cycle_threshold_before_school_threshold(self):
        AcademicPolicy.objects.create(
            school=self.school,
            default_max_score=20,
            default_promotion_threshold=10,
        )
        self.cycle.promotion_threshold_override = 11
        self.cycle.save(update_fields=["promotion_threshold_override"])

        response = self.client.get(
            f"/api/academics/levels/{self.level.id}/",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Decimal(response.data["effective_promotion_threshold"]),
            Decimal("11.00"),
        )

    def test_level_override_is_returned_as_effective_threshold(self):
        AcademicPolicy.objects.create(
            school=self.school,
            default_max_score=20,
            default_promotion_threshold=10,
        )

        response = self.client.patch(
            f"/api/academics/levels/{self.level.id}/",
            {
                "promotion_threshold_override": "12.00",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Decimal(response.data["effective_promotion_threshold"]),
            Decimal("12.00"),
        )

    def test_period_bootstrap_creates_three_terms(self):
        response = self.client.post(
            "/api/academics/periods/bootstrap/",
            {"academic_year": self.year.id},
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.year.periods.count(), 3)

    def test_cannot_assign_subject_from_another_school(self):
        foreign_subject = Subject.objects.create(
            school=self.other_school,
            name="Mathématiques",
            code="math",
        )

        response = self.client.post(
            "/api/academics/level-subjects/",
            {
                "level": self.level.id,
                "subject": foreign_subject.id,
                "coefficient": "4.000",
                "teaching_language": "DEFAULT",
                "order": 1,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 400)
