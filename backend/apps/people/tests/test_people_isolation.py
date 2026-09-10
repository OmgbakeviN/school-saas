from datetime import date

from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import AcademicYear, Classroom, Cycle, Level, Section
from apps.people.models import Enrollment, Guardian, Student
from apps.tenants.models import School


class PeopleIsolationTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name="École A",
            slug="ecole-a",
        )
        self.school_b = School.objects.create(
            name="École B",
            slug="ecole-b",
        )

        self.user = User.objects.create_user(
            email="people@example.com",
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
                "email": "people@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )
        self.assertEqual(login.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

        self.year_a = AcademicYear.objects.create(
            school=self.school_a,
            name="2026/2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_active=True,
        )
        section_a = Section.objects.create(
            school=self.school_a,
            name="Francophone",
            code="fr",
        )
        cycle_a = Cycle.objects.create(
            school=self.school_a,
            section=section_a,
            name="Secondaire",
            code="sec",
        )
        level_a = Level.objects.create(
            school=self.school_a,
            cycle=cycle_a,
            name="3e",
            code="3e",
        )
        self.class_a = Classroom.objects.create(
            school=self.school_a,
            academic_year=self.year_a,
            level=level_a,
            name="3e A",
            code="3e-a",
        )

        self.year_b = AcademicYear.objects.create(
            school=self.school_b,
            name="2026/2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_active=True,
        )
        section_b = Section.objects.create(
            school=self.school_b,
            name="Francophone",
            code="fr",
        )
        cycle_b = Cycle.objects.create(
            school=self.school_b,
            section=section_b,
            name="Secondaire",
            code="sec",
        )
        level_b = Level.objects.create(
            school=self.school_b,
            cycle=cycle_b,
            name="3e",
            code="3e",
        )
        self.class_b = Classroom.objects.create(
            school=self.school_b,
            academic_year=self.year_b,
            level=level_b,
            name="3e B",
            code="3e-b",
        )

    def test_students_are_scoped_to_current_school(self):
        Student.objects.create(
            school=self.school_a,
            matricule="A-001",
            first_name="Alice",
            last_name="A",
        )
        Student.objects.create(
            school=self.school_b,
            matricule="B-001",
            first_name="Bob",
            last_name="B",
        )

        response = self.client.get(
            "/api/people/students/",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["matricule"], "A-001")

    def test_cannot_enroll_student_into_foreign_classroom(self):
        student = Student.objects.create(
            school=self.school_a,
            matricule="A-002",
            first_name="Claire",
            last_name="A",
        )

        response = self.client.post(
            "/api/people/enrollments/",
            {
                "student": student.id,
                "academic_year": self.year_a.id,
                "classroom": self.class_b.id,
                "status": "ACTIVE",
                "promotion_decision": "PENDING",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_enrollment_classroom_must_match_year(self):
        second_year = AcademicYear.objects.create(
            school=self.school_a,
            name="2027/2028",
            start_date=date(2027, 9, 1),
            end_date=date(2028, 6, 30),
        )
        student = Student.objects.create(
            school=self.school_a,
            matricule="A-003",
            first_name="David",
            last_name="A",
        )

        response = self.client.post(
            "/api/people/enrollments/",
            {
                "student": student.id,
                "academic_year": second_year.id,
                "classroom": self.class_a.id,
                "status": "ACTIVE",
                "promotion_decision": "PENDING",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_student_can_only_have_one_enrollment_per_year(self):
        student = Student.objects.create(
            school=self.school_a,
            matricule="A-004",
            first_name="Emma",
            last_name="A",
        )
        Enrollment.objects.create(
            school=self.school_a,
            student=student,
            academic_year=self.year_a,
            classroom=self.class_a,
        )

        response = self.client.post(
            "/api/people/enrollments/",
            {
                "student": student.id,
                "academic_year": self.year_a.id,
                "classroom": self.class_a.id,
                "status": "ACTIVE",
                "promotion_decision": "PENDING",
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_guardian_link_rejects_foreign_guardian(self):
        student = Student.objects.create(
            school=self.school_a,
            matricule="A-005",
            first_name="Franck",
            last_name="A",
        )
        guardian = Guardian.objects.create(
            school=self.school_b,
            first_name="Parent",
            last_name="B",
            phone="600000000",
        )

        response = self.client.post(
            "/api/people/guardian-links/",
            {
                "student": student.id,
                "guardian": guardian.id,
                "relationship": "GUARDIAN",
                "is_primary": True,
                "receives_notifications": True,
                "can_receive_results": True,
            },
            format="json",
            HTTP_HOST="ecole-a.localhost",
        )

        self.assertEqual(response.status_code, 400)
