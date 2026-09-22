from datetime import date
from decimal import Decimal

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.academics.models import (
    AcademicPeriod,
    AcademicYear,
    Classroom,
    Cycle,
    Level,
    Section,
)
from apps.finance.models import (
    StudentTuitionAccount,
    TuitionInstallment,
    TuitionPlan,
)
from apps.people.models import Enrollment, Guardian, Student, StudentGuardian
from apps.report_cards.models import ReportCardSnapshot
from apps.tenants.models import School
from apps.whatsapp_ai.models import (
    GuardianWhatsAppIdentity,
    StudentGuardianDocumentPermission,
    WhatsAppConnection,
)
from apps.whatsapp_ai.phone import normalize_phone


@override_settings(
    WHATSAPP_AGENT_API_KEY="test-agent-key",
    WHATSAPP_AI_DRY_RUN=True,
    WHATSAPP_DEFAULT_COUNTRY_CODE="237",
)
class ParentDocumentsAgentTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="BE WISE WhatsApp Test",
            slug="whatsapp-test",
            city="Yaoundé",
        )
        self.user = User.objects.create_user(
            email="publisher@example.com",
            password="Password123!",
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
            code="wa-fr",
            language=Section.Language.FRENCH,
        )
        self.cycle = Cycle.objects.create(
            school=self.school,
            section=self.section,
            name="Primaire",
            code="wa-primary",
            kind=Cycle.Kind.PRIMARY,
        )
        self.level = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="CM2",
            code="wa-cm2",
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level,
            name="CM2 A",
            code="wa-cm2-a",
        )
        self.period = AcademicPeriod.objects.create(
            school=self.school,
            academic_year=self.year,
            name="1er trimestre",
            code="wa-t1",
            kind=AcademicPeriod.Kind.TRIMESTER,
            order=1,
        )
        self.student = Student.objects.create(
            school=self.school,
            matricule="WA-001",
            first_name="Kevin",
            last_name="Omgba",
        )
        self.enrollment = Enrollment.objects.create(
            school=self.school,
            student=self.student,
            academic_year=self.year,
            classroom=self.classroom,
        )
        self.guardian = Guardian.objects.create(
            school=self.school,
            first_name="Mireille",
            last_name="Omgba",
            phone="690000001",
            preferred_language="FR",
        )
        self.link = StudentGuardian.objects.create(
            school=self.school,
            student=self.student,
            guardian=self.guardian,
            relationship=StudentGuardian.Relationship.MOTHER,
            is_primary=True,
            can_receive_results=True,
        )
        self.connection = WhatsAppConnection.objects.create(
            school=self.school,
            instance_name="whatsapp-test-instance",
        )
        GuardianWhatsAppIdentity.objects.create(
            school=self.school,
            guardian=self.guardian,
            normalized_phone="+237690000001",
            phone_verified=True,
            whatsapp_enabled=True,
        )
        StudentGuardianDocumentPermission.objects.create(
            school=self.school,
            student_guardian=self.link,
            can_receive_report_cards=True,
            can_receive_finance=True,
        )

        self.snapshot = ReportCardSnapshot.objects.create(
            school=self.school,
            enrollment=self.enrollment,
            academic_year=self.year,
            academic_period=self.period,
            report_type=ReportCardSnapshot.ReportType.PERIOD,
            version=1,
            payload={"schema_version": 1},
            payload_sha256="a" * 64,
            pdf_file=ContentFile(b"%PDF-1.4\n% test\n", name="bulletin.pdf"),
            pdf_sha256="b" * 64,
            published_by=self.user,
        )

        self.plan = TuitionPlan.objects.create(
            school=self.school,
            academic_year=self.year,
            name="Pension CM2",
            currency="XAF",
            level=self.level,
        )
        TuitionInstallment.objects.create(
            plan=self.plan,
            name="1ère tranche",
            amount=Decimal("80000.00"),
            due_date=date(2026, 9, 30),
            order=1,
        )
        TuitionInstallment.objects.create(
            plan=self.plan,
            name="2ème tranche",
            amount=Decimal("70000.00"),
            due_date=date(2027, 1, 15),
            order=2,
        )
        StudentTuitionAccount.objects.create(
            school=self.school,
            enrollment=self.enrollment,
            plan=self.plan,
        )

        self.client = APIClient()
        self.auth = {"HTTP_X_BEWISE_AGENT_KEY": "test-agent-key"}

    def test_phone_normalization_cameroon(self):
        self.assertEqual(normalize_phone("690 00 00 01"), "+237690000001")
        self.assertEqual(
            normalize_phone("237690000001@s.whatsapp.net"),
            "+237690000001",
        )

    def test_context_only_exposes_authorized_children_and_documents(self):
        response = self.client.post(
            "/api/whatsapp-ai/context/",
            {
                "instance_name": self.connection.instance_name,
                "phone": "237690000001",
                "message_text": "Envoie-moi le bulletin du 1er trimestre",
            },
            format="json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["authorized"])
        self.assertEqual(len(response.data["children"]), 1)
        child = response.data["children"][0]
        self.assertEqual(child["student_id"], self.student.id)
        self.assertTrue(child["permissions"]["report_cards"])
        self.assertTrue(child["permissions"]["finance"])
        self.assertEqual(
            child["available_report_cards"][0]["period_order"],
            1,
        )
        self.assertTrue(child["tuition_invoice_available"])

    def test_unknown_phone_gets_no_private_context(self):
        response = self.client.post(
            "/api/whatsapp-ai/context/",
            {
                "instance_name": self.connection.instance_name,
                "phone": "237699999999",
            },
            format="json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["authorized"])
        self.assertNotIn("children", response.data)

    def test_report_card_tool_sends_only_published_snapshot(self):
        response = self.client.post(
            "/api/whatsapp-ai/tools/send-term-report-card/",
            {
                "instance_name": self.connection.instance_name,
                "phone": "237690000001",
                "student_id": self.student.id,
                "period": "1er trimestre",
            },
            format="json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["sent"])
        self.assertTrue(response.data["dry_run"])
        self.assertEqual(response.data["period"], "1er trimestre")

    def test_tuition_invoice_tool_generates_pdf_and_dry_run_send(self):
        preview = self.client.post(
            "/api/whatsapp-ai/tools/preview-tuition-invoice/",
            {
                "instance_name": self.connection.instance_name,
                "phone": "237690000001",
                "student_id": self.student.id,
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview["Content-Type"], "application/pdf")
        self.assertEqual(preview.content[:4], b"%PDF")

        response = self.client.post(
            "/api/whatsapp-ai/tools/send-tuition-invoice/",
            {
                "instance_name": self.connection.instance_name,
                "phone": "237690000001",
                "student_id": self.student.id,
            },
            format="json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["sent"])
        self.assertTrue(response.data["dry_run"])
        self.assertEqual(response.data["document_type"], "TUITION_INVOICE")

    def test_missing_internal_key_is_denied(self):
        response = self.client.get("/api/whatsapp-ai/health/")
        self.assertEqual(response.status_code, 403)
