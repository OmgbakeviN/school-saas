from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import Cycle, Level, LevelSubject, Section, Subject
from apps.tenants.models import School


class BulkSubjectAssignmentTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="École Bulk",
            slug="ecole-bulk",
        )
        self.user = User.objects.create_user(
            email="bulk@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.user,
            role=SchoolMembership.Role.DIRECTOR,
        )

        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "bulk@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="ecole-bulk.localhost",
        )
        self.assertEqual(login.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

        section = Section.objects.create(
            school=self.school,
            name="Section francophone",
            code="fr",
        )
        cycle = Cycle.objects.create(
            school=self.school,
            section=section,
            name="Secondaire",
            code="secondaire",
        )
        self.level_1 = Level.objects.create(
            school=self.school,
            cycle=cycle,
            name="6e",
            code="6e",
        )
        self.level_2 = Level.objects.create(
            school=self.school,
            cycle=cycle,
            name="5e",
            code="5e",
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathématiques",
            code="math",
        )

    def test_assign_one_subject_to_multiple_levels(self):
        response = self.client.post(
            "/api/academics/level-subjects/bulk/",
            {
                "subject": self.subject.id,
                "levels": [self.level_1.id, self.level_2.id],
                "coefficient": "4.000",
                "max_score_override": None,
                "teaching_language": "DEFAULT",
                "order": 0,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="ecole-bulk.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created_count"], 2)
        self.assertEqual(response.data["updated_count"], 0)
        self.assertEqual(
            LevelSubject.objects.filter(
                school=self.school,
                subject=self.subject,
            ).count(),
            2,
        )

    def test_bulk_assignment_updates_existing_level_configuration(self):
        LevelSubject.objects.create(
            school=self.school,
            level=self.level_1,
            subject=self.subject,
            coefficient="1.000",
        )

        response = self.client.post(
            "/api/academics/level-subjects/bulk/",
            {
                "subject": self.subject.id,
                "levels": [self.level_1.id, self.level_2.id],
                "coefficient": "3.000",
                "max_score_override": "20.00",
                "teaching_language": "FRENCH",
                "order": 0,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="ecole-bulk.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created_count"], 1)
        self.assertEqual(response.data["updated_count"], 1)

        existing = LevelSubject.objects.get(
            school=self.school,
            level=self.level_1,
            subject=self.subject,
        )
        self.assertEqual(str(existing.coefficient), "3.000")
