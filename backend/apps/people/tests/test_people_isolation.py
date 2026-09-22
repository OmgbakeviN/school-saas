from datetime import date
from io import BytesIO
import tempfile

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import AcademicYear, Classroom, Cycle, Level, Section
from apps.people.models import Enrollment, Guardian, Student, StudentGuardian
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



class StudentPhotoTests(APITestCase):
    def setUp(self):
        self._temp_media = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._temp_media.name)
        self._override.enable()

        self.school = School.objects.create(
            name="Photo School",
            slug="photo-school",
        )
        self.user = User.objects.create_user(
            email="photo@example.com",
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
                "email": "photo@example.com",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="photo-school.localhost",
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
            is_active=True,
        )
        section = Section.objects.create(
            school=self.school,
            name="Francophone",
            code="fr-photo",
        )
        cycle = Cycle.objects.create(
            school=self.school,
            section=section,
            name="Primaire",
            code="pri-photo",
        )
        level = Level.objects.create(
            school=self.school,
            cycle=cycle,
            name="CM2",
            code="cm2-photo",
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=level,
            name="CM2 A",
            code="cm2-a-photo",
        )

    def tearDown(self):
        self._override.disable()
        self._temp_media.cleanup()
        super().tearDown()

    def _jpeg_upload(self, name="student-large.jpg", size=(2400, 1800)):
        image = Image.new("RGB", size, "#8aa4c6")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=96)
        return SimpleUploadedFile(
            name,
            buffer.getvalue(),
            content_type="image/jpeg",
        )

    def test_student_photo_is_compressed_and_exposed_in_profile(self):
        student = Student.objects.create(
            school=self.school,
            matricule="A-PHOTO-001",
            first_name="Photo",
            last_name="Student",
        )

        response = self.client.post(
            f"/api/people/students/{student.id}/photo/",
            {"photo": self._jpeg_upload()},
            format="multipart",
            HTTP_HOST="photo-school.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["photo_url"])
        self.assertEqual(response.data["photo_meta"]["format"], "WEBP")
        self.assertLessEqual(response.data["photo_meta"]["width"], 900)
        self.assertLessEqual(response.data["photo_meta"]["height"], 900)

        student.refresh_from_db()
        self.assertTrue(student.photo.name.endswith(".webp"))
        self.assertLessEqual(student.photo.size, 600 * 1024)

        with student.photo.open("rb") as handle:
            stored = Image.open(handle)
            self.assertEqual(stored.format, "WEBP")
            self.assertLessEqual(max(stored.size), 900)

    def test_student_photo_delete(self):
        student = Student.objects.create(
            school=self.school,
            matricule="A-PHOTO-002",
            first_name="Photo",
            last_name="Delete",
        )
        upload = self.client.post(
            f"/api/people/students/{student.id}/photo/",
            {"photo": self._jpeg_upload()},
            format="multipart",
            HTTP_HOST="photo-school.localhost",
        )
        self.assertEqual(upload.status_code, 200)

        response = self.client.delete(
            f"/api/people/students/{student.id}/photo/",
            HTTP_HOST="photo-school.localhost",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["photo_url"])

    def test_guardian_profile_lists_linked_children(self):
        student = Student.objects.create(
            school=self.school,
            matricule="A-CHILD-001",
            first_name="Junior",
            last_name="Parent",
        )
        Enrollment.objects.create(
            school=self.school,
            student=student,
            academic_year=self.year,
            classroom=self.classroom,
        )
        guardian = Guardian.objects.create(
            school=self.school,
            first_name="Marie",
            last_name="Parent",
            phone="699000001",
        )
        StudentGuardian.objects.create(
            school=self.school,
            student=student,
            guardian=guardian,
            relationship=StudentGuardian.Relationship.MOTHER,
            is_primary=True,
        )

        response = self.client.get(
            f"/api/people/guardians/{guardian.id}/",
            HTTP_HOST="photo-school.localhost",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["children"]), 1)
        self.assertEqual(response.data["children"][0]["matricule"], "A-CHILD-001")
        self.assertEqual(response.data["children"][0]["classroom"], self.classroom.name)
