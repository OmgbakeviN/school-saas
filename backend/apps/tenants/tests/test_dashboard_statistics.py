from datetime import date

from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import (
    AcademicPeriod,
    AcademicYear,
    Classroom,
    Cycle,
    Level,
    Section,
    Subject,
)
from apps.assessments.models import Assessment, Grade
from apps.people.models import Enrollment, Student, Teacher
from apps.teaching.models import TeachingAssignment
from apps.tenants.models import School


class DashboardStatisticsTests(APITestCase):
    host = "stats-school.localhost"

    def setUp(self):
        self.school = School.objects.create(
            name="Stats School",
            slug="stats-school",
        )
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026/2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_active=True,
        )
        self.section = Section.objects.create(
            school=self.school,
            name="Francophone",
            code="fr",
        )
        self.cycle = Cycle.objects.create(
            school=self.school,
            section=self.section,
            name="Primaire",
            code="primary",
            kind=Cycle.Kind.PRIMARY,
        )
        self.level = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="CM2",
            code="cm2",
        )
        self.class_a = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level,
            name="CM2 A",
            code="cm2-a",
            capacity=40,
        )
        self.class_b = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level,
            name="CM2 B",
            code="cm2-b",
            capacity=40,
        )
        self.period = AcademicPeriod.objects.create(
            school=self.school,
            academic_year=self.year,
            name="1er trimestre",
            code="t1",
            order=1,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 20),
        )

        self.student_a = Student.objects.create(
            school=self.school,
            matricule="STA-001",
            first_name="Alice",
            last_name="A",
            gender=Student.Gender.FEMALE,
        )
        self.student_b = Student.objects.create(
            school=self.school,
            matricule="STB-001",
            first_name="Bob",
            last_name="B",
            gender=Student.Gender.MALE,
        )
        self.enrollment_a = Enrollment.objects.create(
            school=self.school,
            student=self.student_a,
            academic_year=self.year,
            classroom=self.class_a,
        )
        self.enrollment_b = Enrollment.objects.create(
            school=self.school,
            student=self.student_b,
            academic_year=self.year,
            classroom=self.class_b,
        )

        self.director = User.objects.create_user(
            email="director-stats@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.director,
            role=SchoolMembership.Role.DIRECTOR,
        )

        self.teacher_user = User.objects.create_user(
            email="teacher-stats@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.teacher_user,
            role=SchoolMembership.Role.TEACHER,
        )
        self.teacher = Teacher.objects.create(
            school=self.school,
            user=self.teacher_user,
            employee_number="T-001",
            first_name="Teacher",
            last_name="One",
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathématiques",
            code="math",
        )
        self.assignment = TeachingAssignment.objects.create(
            school=self.school,
            academic_year=self.year,
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.class_a,
        )
        self.assessment = Assessment.objects.create(
            school=self.school,
            teaching_assignment=self.assignment,
            academic_period=self.period,
            title="Devoir 1",
            status=Assessment.Status.PUBLISHED,
        )
        Grade.objects.create(
            school=self.school,
            assessment=self.assessment,
            enrollment=self.enrollment_a,
            score=16,
        )

    def _login(self, email):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": email,
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_direction_gets_school_wide_statistics(self):
        self._login("director-stats@example.com")

        response = self.client.get(
            "/api/tenant/dashboard/",
            HTTP_HOST=self.host,
        )

        self.assertEqual(response.status_code, 200)
        analytics = response.data["analytics"]

        self.assertEqual(analytics["scope"], "SCHOOL")
        self.assertEqual(analytics["academic_year"]["id"], self.year.id)
        self.assertEqual(analytics["overview"]["students"], 2)
        self.assertEqual(analytics["overview"]["classes"], 2)
        self.assertEqual(
            analytics["academics"]["assessments_total"],
            1,
        )
        self.assertEqual(
            analytics["academics"]["publication_rate"],
            100.0,
        )

    def test_teacher_statistics_are_limited_to_assigned_classes(self):
        self._login("teacher-stats@example.com")

        response = self.client.get(
            "/api/tenant/dashboard/",
            HTTP_HOST=self.host,
        )

        self.assertEqual(response.status_code, 200)
        analytics = response.data["analytics"]

        self.assertEqual(analytics["scope"], "TEACHER")
        self.assertEqual(analytics["overview"]["students"], 1)
        self.assertEqual(analytics["overview"]["classes"], 1)
        self.assertEqual(
            analytics["teacher"]["assignments_count"],
            1,
        )
        self.assertEqual(
            analytics["academics"]["assessments_total"],
            1,
        )
        self.assertIsNone(analytics["finance"])

    def test_direction_can_drill_down_into_class_statistics(self):
        self._login("director-stats@example.com")

        response = self.client.get(
            (
                "/api/tenant/dashboard/classrooms/"
                f"{self.class_a.id}/statistics/"
            ),
            HTTP_HOST=self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["classroom"]["id"],
            self.class_a.id,
        )
        self.assertEqual(
            response.data["population"]["students"],
            1,
        )
        self.assertEqual(
            response.data["population"]["occupancy_rate"],
            2.5,
        )
        self.assertEqual(
            response.data["teaching"]["teachers_count"],
            1,
        )
        self.assertEqual(
            response.data["teaching"]["subjects_count"],
            1,
        )
        self.assertEqual(
            response.data["academics"]["assessments_total"],
            1,
        )
        self.assertEqual(
            response.data["academics"]["publication_rate"],
            100.0,
        )
        self.assertEqual(
            response.data["academics"]["subjects"][0][
                "average_on_20"
            ],
            16.0,
        )

    def test_teacher_can_open_assigned_class_statistics(self):
        self._login("teacher-stats@example.com")

        response = self.client.get(
            (
                "/api/tenant/dashboard/classrooms/"
                f"{self.class_a.id}/statistics/"
            ),
            HTTP_HOST=self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["finance"])
        self.assertIsNotNone(response.data["academics"])

    def test_teacher_cannot_open_unassigned_class_statistics(self):
        self._login("teacher-stats@example.com")

        response = self.client.get(
            (
                "/api/tenant/dashboard/classrooms/"
                f"{self.class_b.id}/statistics/"
            ),
            HTTP_HOST=self.host,
        )

        self.assertEqual(response.status_code, 403)

