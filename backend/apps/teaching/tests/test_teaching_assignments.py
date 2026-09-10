from datetime import date

from rest_framework.test import APITestCase

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import (
    AcademicYear,
    Classroom,
    Cycle,
    Level,
    LevelSubject,
    Section,
    Subject,
)
from apps.people.models import Teacher
from apps.tenants.models import School
from apps.teaching.models import ClassroomLeadership, TeachingAssignment
from apps.teaching.services import teacher_can_enter_scores


class TeachingAssignmentTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="BE WISE Test School",
            slug="bewise-test",
        )
        self.other_school = School.objects.create(
            name="Other School",
            slug="other-school",
        )

        self.owner = User.objects.create_user(
            email="owner@bewise.test",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.owner,
            role=SchoolMembership.Role.OWNER,
        )

        login = self.client.post(
            "/api/auth/login/",
            {
                "email": "owner@bewise.test",
                "password": "Password123!",
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
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
        self.level = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="3e",
            code="3e",
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level,
            name="3e A",
            code="3e-a",
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathématiques",
            code="maths",
        )
        LevelSubject.objects.create(
            school=self.school,
            level=self.level,
            subject=self.subject,
            coefficient=4,
        )
        self.teacher = Teacher.objects.create(
            school=self.school,
            employee_number="TCH-001",
            first_name="Alice",
            last_name="Nana",
            email="alice@example.com",
        )

    def test_create_teacher_subject_class_year_assignment(self):
        response = self.client.post(
            "/api/teaching/assignments/",
            {
                "academic_year": self.year.id,
                "teacher": self.teacher.id,
                "subject": self.subject.id,
                "classroom": self.classroom.id,
                "can_enter_scores": True,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(TeachingAssignment.objects.count(), 1)

    def test_reject_subject_not_configured_for_class_level(self):
        subject = Subject.objects.create(
            school=self.school,
            name="Physique",
            code="physics",
        )

        response = self.client.post(
            "/api/teaching/assignments/",
            {
                "academic_year": self.year.id,
                "teacher": self.teacher.id,
                "subject": subject.id,
                "classroom": self.classroom.id,
                "can_enter_scores": True,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_classroom_leadership_is_unique_per_role(self):
        ClassroomLeadership.objects.create(
            school=self.school,
            academic_year=self.year,
            classroom=self.classroom,
            teacher=self.teacher,
            role=ClassroomLeadership.Role.HOMEROOM_TEACHER,
        )
        other_teacher = Teacher.objects.create(
            school=self.school,
            employee_number="TCH-002",
            first_name="Paul",
            last_name="Essomba",
        )

        response = self.client.post(
            "/api/teaching/leaderships/",
            {
                "academic_year": self.year.id,
                "classroom": self.classroom.id,
                "teacher": other_teacher.id,
                "role": "HOMEROOM_TEACHER",
                "is_active": True,
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 400)

    def test_teacher_account_provision_and_login(self):
        response = self.client.post(
            f"/api/teaching/teachers/{self.teacher.id}/account/",
            {
                "email": "alice.teacher@example.com",
                "password": "Teacher123!",
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 201)
        self.teacher.refresh_from_db()
        self.assertIsNotNone(self.teacher.user_id)
        self.assertTrue(
            SchoolMembership.objects.filter(
                school=self.school,
                user=self.teacher.user,
                role=SchoolMembership.Role.TEACHER,
                is_active=True,
            ).exists()
        )

        teacher_client = self.client_class()
        login = teacher_client.post(
            "/api/auth/login/",
            {
                "email": "alice.teacher@example.com",
                "password": "Teacher123!",
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["membership"]["role"], "TEACHER")

    def test_teacher_can_only_enter_scores_for_exact_assignment(self):
        teacher_user = User.objects.create_user(
            email="teacher2@example.com",
            password="Teacher123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=teacher_user,
            role=SchoolMembership.Role.TEACHER,
        )
        self.teacher.user = teacher_user
        self.teacher.save(update_fields=["user"])

        TeachingAssignment.objects.create(
            school=self.school,
            academic_year=self.year,
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            can_enter_scores=True,
        )

        self.assertTrue(
            teacher_can_enter_scores(
                user=teacher_user,
                school=self.school,
                academic_year_id=self.year.id,
                classroom_id=self.classroom.id,
                subject_id=self.subject.id,
            )
        )

        other_subject = Subject.objects.create(
            school=self.school,
            name="Français",
            code="francais",
        )
        self.assertFalse(
            teacher_can_enter_scores(
                user=teacher_user,
                school=self.school,
                academic_year_id=self.year.id,
                classroom_id=self.classroom.id,
                subject_id=other_subject.id,
            )
        )

    def test_teacher_me_endpoint_only_returns_own_assignments(self):
        teacher_user = User.objects.create_user(
            email="teacher3@example.com",
            password="Teacher123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=teacher_user,
            role=SchoolMembership.Role.TEACHER,
        )
        self.teacher.user = teacher_user
        self.teacher.save(update_fields=["user"])

        TeachingAssignment.objects.create(
            school=self.school,
            academic_year=self.year,
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            can_enter_scores=True,
        )

        teacher_client = self.client_class()
        login = teacher_client.post(
            "/api/auth/login/",
            {
                "email": "teacher3@example.com",
                "password": "Teacher123!",
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )
        teacher_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

        response = teacher_client.get(
            "/api/teaching/me/",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["assignments"]), 1)
        self.assertEqual(
            response.data["assignments"][0]["subject"],
            self.subject.id,
        )

    def test_primary_class_teacher_receives_all_level_subjects_automatically(self):
        self.school.teaching_model = School.TeachingModel.CLASS_TEACHER
        self.school.education_level = School.EducationLevel.PRIMARY
        self.school.save(update_fields=["teaching_model", "education_level"])

        second_subject = Subject.objects.create(
            school=self.school,
            name="Français",
            code="francais-primary",
        )
        LevelSubject.objects.create(
            school=self.school,
            level=self.level,
            subject=second_subject,
            coefficient=4,
        )

        teacher_user = User.objects.create_user(
            email="primary.teacher@example.com",
            password="Teacher123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=teacher_user,
            role=SchoolMembership.Role.TEACHER,
        )
        self.teacher.user = teacher_user
        self.teacher.save(update_fields=["user"])

        response = self.client.post(
            "/api/teaching/leaderships/",
            {
                "academic_year": self.year.id,
                "classroom": self.classroom.id,
                "teacher": self.teacher.id,
                "role": ClassroomLeadership.Role.CLASS_TEACHER,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 201)

        generated = TeachingAssignment.objects.filter(
            school=self.school,
            teacher=self.teacher,
            classroom=self.classroom,
            academic_year=self.year,
            source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
            is_active=True,
        )

        self.assertEqual(generated.count(), 2)
        self.assertSetEqual(
            set(generated.values_list("subject_id", flat=True)),
            {self.subject.id, second_subject.id},
        )

        self.assertTrue(
            teacher_can_enter_scores(
                user=teacher_user,
                school=self.school,
                academic_year_id=self.year.id,
                classroom_id=self.classroom.id,
                subject_id=self.subject.id,
            )
        )
        self.assertTrue(
            teacher_can_enter_scores(
                user=teacher_user,
                school=self.school,
                academic_year_id=self.year.id,
                classroom_id=self.classroom.id,
                subject_id=second_subject.id,
            )
        )

    def test_homeroom_teacher_does_not_receive_subject_access(self):
        self.school.teaching_model = School.TeachingModel.CLASS_TEACHER
        self.school.save(update_fields=["teaching_model"])

        teacher_user = User.objects.create_user(
            email="homeroom.teacher@example.com",
            password="Teacher123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=teacher_user,
            role=SchoolMembership.Role.TEACHER,
        )
        self.teacher.user = teacher_user
        self.teacher.save(update_fields=["user"])

        response = self.client.post(
            "/api/teaching/leaderships/",
            {
                "academic_year": self.year.id,
                "classroom": self.classroom.id,
                "teacher": self.teacher.id,
                "role": ClassroomLeadership.Role.HOMEROOM_TEACHER,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(
            TeachingAssignment.objects.filter(
                school=self.school,
                teacher=self.teacher,
                classroom=self.classroom,
                source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
                is_active=True,
            ).exists()
        )
        self.assertFalse(
            teacher_can_enter_scores(
                user=teacher_user,
                school=self.school,
                academic_year_id=self.year.id,
                classroom_id=self.classroom.id,
                subject_id=self.subject.id,
            )
        )

    def test_removing_class_teacher_deactivates_automatic_assignments(self):
        self.school.teaching_model = School.TeachingModel.CLASS_TEACHER
        self.school.save(update_fields=["teaching_model"])

        create = self.client.post(
            "/api/teaching/leaderships/",
            {
                "academic_year": self.year.id,
                "classroom": self.classroom.id,
                "teacher": self.teacher.id,
                "role": ClassroomLeadership.Role.CLASS_TEACHER,
                "is_active": True,
            },
            format="json",
            HTTP_HOST="bewise-test.localhost",
        )
        self.assertEqual(create.status_code, 201)

        self.assertTrue(
            TeachingAssignment.objects.filter(
                school=self.school,
                classroom=self.classroom,
                source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
                is_active=True,
            ).exists()
        )

        delete = self.client.delete(
            f"/api/teaching/leaderships/{create.data['id']}/",
            HTTP_HOST="bewise-test.localhost",
        )
        self.assertEqual(delete.status_code, 204)

        self.assertFalse(
            TeachingAssignment.objects.filter(
                school=self.school,
                classroom=self.classroom,
                source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
                is_active=True,
            ).exists()
        )

    def test_existing_class_teacher_is_synced_when_teacher_opens_my_teaching(self):
        self.school.teaching_model = School.TeachingModel.CLASS_TEACHER
        self.school.save(update_fields=["teaching_model"])

        teacher_user = User.objects.create_user(
            email="existing.primary@example.com",
            password="Teacher123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=teacher_user,
            role=SchoolMembership.Role.TEACHER,
        )
        self.teacher.user = teacher_user
        self.teacher.save(update_fields=["user"])

        # Simulates a titular created before STEP 05.1.
        ClassroomLeadership.objects.create(
            school=self.school,
            academic_year=self.year,
            classroom=self.classroom,
            teacher=self.teacher,
            role=ClassroomLeadership.Role.CLASS_TEACHER,
            is_active=True,
        )

        teacher_client = self.client_class()
        teacher_client.force_authenticate(user=teacher_user)

        response = teacher_client.get(
            "/api/teaching/me/",
            HTTP_HOST="bewise-test.localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["assignments"]), 1)
        self.assertTrue(response.data["assignments"][0]["is_automatic"])
        self.assertEqual(
            response.data["assignments"][0]["source"],
            TeachingAssignment.Source.CLASS_TEACHER_AUTO,
        )
