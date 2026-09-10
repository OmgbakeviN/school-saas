from datetime import date
from rest_framework.test import APITestCase
from apps.accounts.models import SchoolMembership, User
from apps.academics.models import AcademicPeriod, AcademicYear, Classroom, Cycle, Level, LevelSubject, Section, Subject
from apps.people.models import Enrollment, Student, Teacher
from apps.teaching.models import ClassroomLeadership, TeachingAssignment
from apps.tenants.models import School
from apps.assessments.models import Assessment


class AssessmentWorkflowTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School", slug="test-school")
        self.director = User.objects.create_user(email="dir@test.com", password="Password123!")
        self.teacher_user = User.objects.create_user(email="teacher@test.com", password="Password123!")
        SchoolMembership.objects.create(school=self.school, user=self.director, role="DIRECTOR")
        SchoolMembership.objects.create(school=self.school, user=self.teacher_user, role="TEACHER")
        self.year = AcademicYear.objects.create(school=self.school, name="2026/2027", start_date=date(2026,9,1), end_date=date(2027,6,30), is_active=True)
        self.period = AcademicPeriod.objects.create(school=self.school, academic_year=self.year, name="Trimestre 1", code="t1")
        section = Section.objects.create(school=self.school, name="FR", code="fr")
        cycle = Cycle.objects.create(school=self.school, section=section, name="Secondaire", code="sec")
        level = Level.objects.create(school=self.school, cycle=cycle, name="3e", code="3e")
        self.classroom = Classroom.objects.create(school=self.school, academic_year=self.year, level=level, name="3e A", code="3e-a")
        self.subject = Subject.objects.create(school=self.school, name="Mathématiques", code="math")
        LevelSubject.objects.create(school=self.school, level=level, subject=self.subject, coefficient=4)
        self.teacher = Teacher.objects.create(school=self.school, user=self.teacher_user, employee_number="T-1", first_name="Paul", last_name="Test")
        self.assignment = TeachingAssignment.objects.create(school=self.school, academic_year=self.year, teacher=self.teacher, subject=self.subject, classroom=self.classroom, can_enter_scores=True)
        for idx in range(2):
            student = Student.objects.create(school=self.school, matricule=f"S-{idx}", first_name=f"E{idx}", last_name="Test")
            Enrollment.objects.create(school=self.school, student=student, academic_year=self.year, classroom=self.classroom)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def host(self):
        return {"HTTP_HOST": "test-school.localhost"}

    def test_teacher_cannot_open_when_period_closed(self):
        self.auth(self.teacher_user)
        create = self.client.post("/api/assessments/assessments/", {"teaching_assignment": self.assignment.id, "academic_period": self.period.id, "title": "Devoir 1", "max_score": "20.00", "weight": "1.000"}, format="json", **self.host())
        self.assertEqual(create.status_code, 201)
        response = self.client.post(f"/api/assessments/assessments/{create.data['id']}/open/", {}, format="json", **self.host())
        self.assertEqual(response.status_code, 409)

    def test_full_workflow_and_lock(self):
        self.auth(self.director)
        self.client.patch(f"/api/assessments/period-controls/{self.period.id}/", {"score_entry_open": True}, format="json", **self.host())
        self.auth(self.teacher_user)
        create = self.client.post("/api/assessments/assessments/", {"teaching_assignment": self.assignment.id, "academic_period": self.period.id, "title": "Devoir 1", "max_score": "20.00", "weight": "1.000"}, format="json", **self.host())
        aid = create.data["id"]
        self.assertEqual(self.client.post(f"/api/assessments/assessments/{aid}/open/", {}, format="json", **self.host()).status_code, 200)
        gb = self.client.get(f"/api/assessments/assessments/{aid}/gradebook/", **self.host()).data
        payload = {"grades": [{"enrollment": row["enrollment_id"], "score": "15.000"} for row in gb["rows"]]}
        self.assertEqual(self.client.put(f"/api/assessments/assessments/{aid}/gradebook/", payload, format="json", **self.host()).status_code, 200)
        self.assertEqual(self.client.post(f"/api/assessments/assessments/{aid}/submit/", {}, format="json", **self.host()).status_code, 200)
        self.auth(self.director)
        self.assertEqual(self.client.post(f"/api/assessments/assessments/{aid}/validate/", {}, format="json", **self.host()).status_code, 200)
        self.assertEqual(self.client.post(f"/api/assessments/assessments/{aid}/publish/", {}, format="json", **self.host()).status_code, 200)
        self.auth(self.teacher_user)
        self.assertEqual(self.client.put(f"/api/assessments/assessments/{aid}/gradebook/", payload, format="json", **self.host()).status_code, 403)
        self.auth(self.director)
        self.assertEqual(self.client.post(f"/api/assessments/assessments/{aid}/reopen/", {}, format="json", **self.host()).status_code, 200)
        self.auth(self.teacher_user)
        self.assertEqual(self.client.put(f"/api/assessments/assessments/{aid}/gradebook/", payload, format="json", **self.host()).status_code, 200)


    def test_primary_class_teacher_can_create_assessment_for_all_program_subjects(self):
        self.school.teaching_model = School.TeachingModel.CLASS_TEACHER
        self.school.education_level = School.EducationLevel.PRIMARY
        self.school.save(update_fields=["teaching_model", "education_level"])

        french = Subject.objects.create(
            school=self.school,
            name="Français",
            code="french-primary",
        )
        LevelSubject.objects.create(
            school=self.school,
            level=self.classroom.level,
            subject=french,
            coefficient=4,
        )

        # The explicit maths assignment from setUp simulates a pre-existing
        # manual assignment. The second subject must be generated from the
        # class-teacher leadership.
        ClassroomLeadership.objects.create(
            school=self.school,
            academic_year=self.year,
            classroom=self.classroom,
            teacher=self.teacher,
            role=ClassroomLeadership.Role.CLASS_TEACHER,
            is_active=True,
        )

        self.auth(self.teacher_user)

        # /teaching/me/ performs the compatibility sync for leaderships that
        # existed before STEP 05.1.
        access = self.client.get(
            "/api/teaching/me/",
            **self.host(),
        )
        self.assertEqual(access.status_code, 200)

        french_assignment = TeachingAssignment.objects.get(
            school=self.school,
            academic_year=self.year,
            classroom=self.classroom,
            teacher=self.teacher,
            subject=french,
        )
        self.assertEqual(
            french_assignment.source,
            TeachingAssignment.Source.CLASS_TEACHER_AUTO,
        )
        self.assertTrue(french_assignment.can_enter_scores)

        create = self.client.post(
            "/api/assessments/assessments/",
            {
                "teaching_assignment": french_assignment.id,
                "academic_period": self.period.id,
                "title": "Dictée",
                "kind": "TEST",
                "max_score": "20.00",
                "weight": "1.000",
            },
            format="json",
            **self.host(),
        )

        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data["subject"], french.id)
        self.assertEqual(create.data["classroom"], self.classroom.id)

    def test_homeroom_teacher_cannot_create_assessment_without_subject_assignment(self):
        other_subject = Subject.objects.create(
            school=self.school,
            name="Sciences",
            code="science-homeroom",
        )
        LevelSubject.objects.create(
            school=self.school,
            level=self.classroom.level,
            subject=other_subject,
            coefficient=2,
        )

        ClassroomLeadership.objects.create(
            school=self.school,
            academic_year=self.year,
            classroom=self.classroom,
            teacher=self.teacher,
            role=ClassroomLeadership.Role.HOMEROOM_TEACHER,
            is_active=True,
        )

        self.school.teaching_model = School.TeachingModel.CLASS_TEACHER
        self.school.save(update_fields=["teaching_model"])

        self.auth(self.teacher_user)
        self.client.get("/api/teaching/me/", **self.host())

        self.assertFalse(
            TeachingAssignment.objects.filter(
                school=self.school,
                academic_year=self.year,
                classroom=self.classroom,
                teacher=self.teacher,
                subject=other_subject,
            ).exists()
        )
