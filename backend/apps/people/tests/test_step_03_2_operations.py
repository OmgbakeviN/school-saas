from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import (
    AcademicPolicy,
    AcademicYear,
    Classroom,
    Cycle,
    Level,
    Section,
)
from apps.people.models import Enrollment, Student, Teacher, Guardian
from apps.tenants.models import School


class Step032OperationsTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="École STEP 03.2",
            slug="step-03-2",
        )
        self.user = User.objects.create_user(
            email="step032@example.com",
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
                "email": "step032@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="step-03-2.localhost",
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
            name="Francophone",
            code="fr",
        )
        self.cycle = Cycle.objects.create(
            school=self.school,
            section=self.section,
            name="Secondaire",
            code="secondaire",
        )
        self.level_3 = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="3e",
            code="3e",
            order=1,
        )
        self.level_2 = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="2nde",
            code="2nde",
            order=2,
        )

        self.class_3 = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level_3,
            name="3e A",
            code="3e-a",
        )

        AcademicPolicy.objects.create(
            school=self.school,
            default_max_score=20,
            default_promotion_threshold=10,
        )

    def test_bulk_assign_students(self):
        students = [
            Student.objects.create(
                school=self.school,
                matricule=f"S-{index}",
                first_name=f"Student{index}",
                last_name="Test",
            )
            for index in range(1, 4)
        ]

        response = self.client.post(
            "/api/people/bulk/class-assignment/",
            {
                "student_ids": [
                    student.id
                    for student in students
                ],
                "academic_year": self.year.id,
                "classroom": self.class_3.id,
            },
            format="json",
            HTTP_HOST="step-03-2.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created"], 3)

    def test_import_students_csv_dry_run_does_not_save(self):
        upload = SimpleUploadedFile(
            "students.csv",
            (
                "matricule,first_name,last_name,gender\n"
                "CSV-001,Alice,Nana,FEMALE\n"
                "CSV-002,Paul,Essomba,MALE\n"
            ).encode("utf-8"),
            content_type="text/csv",
        )

        response = self.client.post(
            "/api/people/imports/students/",
            {
                "file": upload,
                "dry_run": "true",
            },
            format="multipart",
            HTTP_HOST="step-03-2.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created"], 2)
        self.assertEqual(
            Student.objects.filter(
                school=self.school,
                matricule__startswith="CSV-",
            ).count(),
            0,
        )

    def test_promotion_preview_uses_school_threshold(self):
        student = Student.objects.create(
            school=self.school,
            matricule="PROMO-001",
            first_name="Kevin",
            last_name="Test",
        )
        Enrollment.objects.create(
            school=self.school,
            student=student,
            academic_year=self.year,
            classroom=self.class_3,
            final_average="12.000",
        )

        response = self.client.post(
            "/api/people/promotions/preview/",
            {"academic_year": self.year.id},
            format="json",
            HTTP_HOST="step-03-2.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["items"][0]["suggested_decision"],
            "PROMOTED",
        )

    def test_prepare_new_year_clones_classrooms(self):
        response = self.client.post(
            "/api/people/academic-years/prepare/",
            {
                "source_academic_year": self.year.id,
                "name": "2027/2028",
                "start_date": "2027-09-01",
                "end_date": "2028-06-30",
                "period_system": "TRIMESTER",
                "clone_classrooms": True,
                "clone_periods": False,
                "is_active": False,
            },
            format="json",
            HTTP_HOST="step-03-2.localhost",
        )

        self.assertEqual(response.status_code, 201)
        new_year = AcademicYear.objects.get(
            school=self.school,
            name="2027/2028",
        )
        self.assertTrue(
            Classroom.objects.filter(
                school=self.school,
                academic_year=new_year,
                code="3e-a",
            ).exists()
        )

    def test_apply_promotion_creates_next_enrollment(self):
        new_year = AcademicYear.objects.create(
            school=self.school,
            name="2027/2028",
            start_date=date(2027, 9, 1),
            end_date=date(2028, 6, 30),
        )
        target_class = Classroom.objects.create(
            school=self.school,
            academic_year=new_year,
            level=self.level_2,
            name="2nde A",
            code="2nde-a",
        )

        student = Student.objects.create(
            school=self.school,
            matricule="PROMO-002",
            first_name="Marie",
            last_name="Test",
        )
        source = Enrollment.objects.create(
            school=self.school,
            student=student,
            academic_year=self.year,
            classroom=self.class_3,
            final_average="14.000",
        )

        response = self.client.post(
            "/api/people/promotions/apply/",
            {
                "items": [
                    {
                        "enrollment_id": source.id,
                        "decision": "PROMOTED",
                        "target_classroom": target_class.id,
                        "reason": "",
                    }
                ]
            },
            format="json",
            HTTP_HOST="step-03-2.localhost",
        )

        self.assertEqual(response.status_code, 200)
        source.refresh_from_db()
        self.assertEqual(
            source.promotion_decision,
            "PROMOTED",
        )
        self.assertIsNotNone(source.next_enrollment_id)
        self.assertEqual(
            source.next_enrollment.classroom_id,
            target_class.id,
        )

    def test_student_xlsx_export_is_real_excel_file(self):
        student = Student.objects.create(
            school=self.school,
            matricule="EXP-001",
            first_name="Alice",
            last_name="Export",
        )
        Enrollment.objects.create(
            school=self.school,
            student=student,
            academic_year=self.year,
            classroom=self.class_3,
        )

        response = self.client.get(
            (
                "/api/people/exports/students/"
                f"?format=xlsx&academic_year={self.year.id}"
            ),
            HTTP_HOST="step-03-2.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        self.assertTrue(response.content.startswith(b"PK"))
        self.assertIn(
            'attachment; filename="step-03-2-students.xlsx"',
            response["Content-Disposition"],
        )

    def test_all_export_routes_exist(self):
        Teacher.objects.create(
            school=self.school,
            employee_number="T-001",
            first_name="Teacher",
            last_name="Export",
        )
        Guardian.objects.create(
            school=self.school,
            first_name="Parent",
            last_name="Export",
            phone="699111222",
        )

        urls = [
            "/api/people/exports/students/?format=csv",
            "/api/people/exports/teachers/?format=csv",
            "/api/people/exports/guardians/?format=csv",
            "/api/people/exports/enrollments/?format=csv",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(
                    url,
                    HTTP_HOST="step-03-2.localhost",
                )
                self.assertEqual(response.status_code, 200)
