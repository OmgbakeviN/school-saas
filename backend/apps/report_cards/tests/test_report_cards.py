from datetime import date
from decimal import Decimal
from io import BytesIO
import zipfile

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import (
    AcademicPeriod,
    AcademicYear,
    Classroom,
    Cycle,
    Level,
    LevelSubject,
    Section,
    Subject,
)
from apps.assessments.models import Assessment, Grade
from apps.people.models import Enrollment, Student, Teacher
from apps.report_cards.models import ReportCardSnapshot, ReportCardTemplate
from apps.teaching.models import TeachingAssignment
from apps.tenants.models import School


class ReportCardTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="BE WISE Test School",
            slug="report-test",
            motto="Travail - Discipline - Réussite",
        )
        self.owner = User.objects.create_user(
            email="owner-report@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.owner,
            role=SchoolMembership.Role.OWNER,
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
            code="fr-report",
        )
        self.cycle = Cycle.objects.create(
            school=self.school,
            section=self.section,
            name="Primaire",
            code="primary-report",
            kind=Cycle.Kind.PRIMARY,
        )
        self.level = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="CM2",
            code="cm2-report",
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level,
            name="CM2 A",
            code="cm2-a-report",
        )
        self.period = AcademicPeriod.objects.create(
            school=self.school,
            academic_year=self.year,
            name="1er trimestre",
            code="t1-report",
            order=1,
        )
        self.subject = Subject.objects.create(
            school=self.school,
            name="Mathématiques",
            code="math-report",
        )
        LevelSubject.objects.create(
            school=self.school,
            level=self.level,
            subject=self.subject,
            coefficient=4,
        )
        self.teacher = Teacher.objects.create(
            school=self.school,
            employee_number="T-RPT-1",
            first_name="Alice",
            last_name="Nana",
        )
        self.assignment = TeachingAssignment.objects.create(
            school=self.school,
            academic_year=self.year,
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
        )
        self.assessment = Assessment.objects.create(
            school=self.school,
            teaching_assignment=self.assignment,
            academic_period=self.period,
            title="Composition",
            max_score=20,
            status=Assessment.Status.PUBLISHED,
        )

        self.student = Student.objects.create(
            school=self.school,
            matricule="RPT-001",
            first_name="Kevin",
            last_name="Omgba",
        )
        self.enrollment = Enrollment.objects.create(
            school=self.school,
            student=self.student,
            academic_year=self.year,
            classroom=self.classroom,
        )
        Grade.objects.create(
            school=self.school,
            assessment=self.assessment,
            enrollment=self.enrollment,
            score=Decimal("15"),
            entered_by=self.owner,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.host = {
            "HTTP_HOST": "report-test.localhost",
        }

    def test_period_preview(self):
        response = self.client.get(
            (
                f"/api/report-cards/results/students/"
                f"{self.enrollment.id}/periods/{self.period.id}/"
            ),
            **self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rank"], 1)
        self.assertEqual(len(response.data["subjects"]), 1)

    def test_publish_creates_immutable_pdf_snapshot(self):
        response = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
                "general_comment": "Bon trimestre.",
            },
            format="json",
            **self.host,
        )
        self.assertEqual(response.status_code, 201)

        snapshot = ReportCardSnapshot.objects.get()
        self.assertEqual(snapshot.version, 1)
        self.assertTrue(snapshot.pdf_file.name.endswith(".pdf"))
        self.assertEqual(len(snapshot.payload_sha256), 64)
        self.assertEqual(len(snapshot.pdf_sha256), 64)

        with snapshot.pdf_file.open("rb") as file:
            self.assertEqual(file.read(4), b"%PDF")

    def test_same_publication_does_not_create_a_new_version(self):
        first = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(first.status_code, 201)
        self.assertTrue(first.data["created_new_version"])

        second = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )

        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.data["created_new_version"])
        self.assertTrue(second.data["unchanged"])
        self.assertEqual(second.data["snapshot"]["version"], 1)
        self.assertEqual(ReportCardSnapshot.objects.count(), 1)

    def test_modified_publication_creates_version_two(self):
        first = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
                "general_comment": "Nouvelle appréciation de la direction.",
            },
            format="json",
            **self.host,
        )
        self.assertEqual(second.status_code, 201)
        self.assertTrue(second.data["created_new_version"])
        self.assertEqual(second.data["snapshot"]["version"], 2)

        versions = list(
            ReportCardSnapshot.objects.order_by("version")
            .values_list("version", flat=True)
        )
        self.assertEqual(versions, [1, 2])

    def test_public_verification_does_not_expose_grades(self):
        publish = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(publish.status_code, 201)

        snapshot = ReportCardSnapshot.objects.get()
        public = APIClient().get(
            (
                "/api/public/report-cards/verify/"
                f"{snapshot.verification_token}/"
            ),
            HTTP_HOST="localhost",
        )

        self.assertEqual(public.status_code, 200)
        self.assertTrue(public.data["authentic"])
        self.assertNotIn("subjects", public.data)
        self.assertNotIn("overall_average", public.data)

    def test_dense_ranking_uses_1_1_2(self):
        tied_student = Student.objects.create(
            school=self.school,
            matricule="RPT-002",
            first_name="Alice",
            last_name="Tied",
        )
        tied_enrollment = Enrollment.objects.create(
            school=self.school,
            student=tied_student,
            academic_year=self.year,
            classroom=self.classroom,
        )
        Grade.objects.create(
            school=self.school,
            assessment=self.assessment,
            enrollment=tied_enrollment,
            score=Decimal("15"),
            entered_by=self.owner,
        )

        third_student = Student.objects.create(
            school=self.school,
            matricule="RPT-003",
            first_name="Paul",
            last_name="Third",
        )
        third_enrollment = Enrollment.objects.create(
            school=self.school,
            student=third_student,
            academic_year=self.year,
            classroom=self.classroom,
        )
        Grade.objects.create(
            school=self.school,
            assessment=self.assessment,
            enrollment=third_enrollment,
            score=Decimal("13"),
            entered_by=self.owner,
        )

        response = self.client.get(
            (
                f"/api/report-cards/results/classrooms/"
                f"{self.classroom.id}/periods/{self.period.id}/"
            ),
            **self.host,
        )

        self.assertEqual(response.status_code, 200)

        ranks = {
            item["matricule"]: item["rank"]
            for item in response.data["students"]
        }

        self.assertEqual(ranks["RPT-001"], 1)
        self.assertEqual(ranks["RPT-002"], 1)
        self.assertEqual(ranks["RPT-003"], 2)

    def test_classroom_zip_contains_latest_published_report_cards(self):
        second_student = Student.objects.create(
            school=self.school,
            matricule="RPT-004",
            first_name="Marie",
            last_name="Zip",
        )
        second_enrollment = Enrollment.objects.create(
            school=self.school,
            student=second_student,
            academic_year=self.year,
            classroom=self.classroom,
        )
        Grade.objects.create(
            school=self.school,
            assessment=self.assessment,
            enrollment=second_enrollment,
            score=Decimal("12"),
            entered_by=self.owner,
        )

        publish = self.client.post(
            "/api/report-cards/publish/classroom/",
            {
                "classroom": self.classroom.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(publish.status_code, 201)
        self.assertEqual(publish.data["created"], 2)

        response = self.client.get(
            (
                "/api/report-cards/download/classroom-zip/"
                f"?classroom={self.classroom.id}"
                "&report_type=PERIOD"
                f"&academic_period={self.period.id}"
            ),
            **self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertEqual(response["X-Report-Cards-Included"], "2")
        self.assertEqual(response["X-Report-Cards-Missing"], "0")

        with zipfile.ZipFile(BytesIO(response.content), "r") as archive:
            names = archive.namelist()
            pdf_names = [name for name in names if name.endswith(".pdf")]
            self.assertEqual(len(pdf_names), 2)
            self.assertIn("manifest.txt", names)

    def test_pending_decision_wording_is_explicit(self):
        # Annual results require at least one published period result,
        # which is already available in setUp.
        response = self.client.get(
            (
                f"/api/report-cards/results/students/"
                f"{self.enrollment.id}/annual/"
            ),
            **self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["promotion_decision_label"],
            "Décision de fin d'année non arrêtée",
        )


    def test_preview_pdf_is_one_a4_page_and_creates_no_snapshot(self):
        response = self.client.post(
            "/api/report-cards/preview/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )
        self.assertEqual(response["X-Report-Card-Pages"], "1")
        self.assertEqual(
            response["X-Report-Card-Fits-A4"],
            "true",
        )
        self.assertEqual(
            ReportCardSnapshot.objects.count(),
            0,
        )

    def test_cycle_default_template_is_frozen_in_snapshot(self):
        general = ReportCardTemplate.objects.create(
            school=self.school,
            name="Général",
            template_key=ReportCardTemplate.TemplateKey.CLASSIC,
            is_default=True,
        )
        cycle_template = ReportCardTemplate.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="Primaire compact",
            template_key=ReportCardTemplate.TemplateKey.COMPACT,
            is_default=True,
        )

        response = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )

        self.assertEqual(response.status_code, 201)
        snapshot = ReportCardSnapshot.objects.get()
        self.assertEqual(
            snapshot.payload["template"]["id"],
            cycle_template.id,
        )
        self.assertEqual(
            snapshot.payload["template"]["key"],
            "COMPACT",
        )
        self.assertEqual(
            snapshot.payload["render"]["page_count"],
            1,
        )
        self.assertTrue(
            snapshot.payload["render"]["fits_one_page"]
        )

    def test_template_change_creates_new_report_card_version(self):
        template = ReportCardTemplate.objects.create(
            school=self.school,
            name="Modèle principal",
            template_key=ReportCardTemplate.TemplateKey.CLASSIC,
            is_default=True,
        )

        first = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(first.status_code, 201)

        template.template_key = (
            ReportCardTemplate.TemplateKey.MODERN
        )
        template.version += 1
        template.save()

        second = self.client.post(
            "/api/report-cards/publish/",
            {
                "enrollment": self.enrollment.id,
                "report_type": "PERIOD",
                "academic_period": self.period.id,
            },
            format="json",
            **self.host,
        )

        self.assertEqual(second.status_code, 201)
        self.assertEqual(
            second.data["snapshot"]["version"],
            2,
        )
        self.assertEqual(
            ReportCardSnapshot.objects.count(),
            2,
        )

