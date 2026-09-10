from datetime import date
from decimal import Decimal
from io import BytesIO

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import (
    AcademicYear,
    Classroom,
    Cycle,
    Level,
    Section,
)
from apps.finance.models import (
    PaymentAllocation,
    PaymentReceiptSnapshot,
    StudentTuitionAccount,
    TuitionPayment,
    TuitionPlan,
)
from apps.people.models import Enrollment, Student
from apps.tenants.models import School


class FinanceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="BE WISE Finance School",
            slug="finance-test",
            city="Yaoundé",
        )
        self.owner = User.objects.create_user(
            email="finance-owner@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.owner,
            role=SchoolMembership.Role.OWNER,
        )

        self.accountant = User.objects.create_user(
            email="finance-accountant@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=self.accountant,
            role=SchoolMembership.Role.ACCOUNTANT,
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
            name="English",
            code="finance-en",
        )
        self.cycle = Cycle.objects.create(
            school=self.school,
            section=self.section,
            name="Secondary",
            code="finance-secondary",
            kind=Cycle.Kind.SECONDARY,
        )
        self.level = Level.objects.create(
            school=self.school,
            cycle=self.cycle,
            name="Class 6",
            code="finance-class-6",
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            academic_year=self.year,
            level=self.level,
            name="Class 6 A",
            code="finance-class-6-a",
        )

        self.student = Student.objects.create(
            school=self.school,
            matricule="FIN-001",
            first_name="Victor",
            last_name="Ekani",
        )
        self.enrollment = Enrollment.objects.create(
            school=self.school,
            student=self.student,
            academic_year=self.year,
            classroom=self.classroom,
        )

        self.owner_client = APIClient()
        self.owner_client.force_authenticate(user=self.owner)

        self.accountant_client = APIClient()
        self.accountant_client.force_authenticate(
            user=self.accountant
        )

        self.host = {
            "HTTP_HOST": "finance-test.localhost",
        }

    def create_plan(self):
        response = self.owner_client.post(
            "/api/finance/plans/",
            {
                "academic_year": self.year.id,
                "name": "Pension Class 6",
                "currency": "XAF",
                "level": self.level.id,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(response.status_code, 201)

        plan_id = response.data["id"]

        first = self.owner_client.post(
            f"/api/finance/plans/{plan_id}/installments/",
            {
                "name": "1ère tranche",
                "amount": "50000.00",
                "order": 1,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(first.status_code, 201)

        second = self.owner_client.post(
            f"/api/finance/plans/{plan_id}/installments/",
            {
                "name": "2ème tranche",
                "amount": "40000.00",
                "order": 2,
            },
            format="json",
            **self.host,
        )
        self.assertEqual(second.status_code, 201)

        return TuitionPlan.objects.get(id=plan_id)

    def assign_plan(self, plan):
        response = self.owner_client.post(
            f"/api/finance/plans/{plan.id}/assign/",
            {},
            format="json",
            **self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["created"], 1)
        return StudentTuitionAccount.objects.get(
            enrollment=self.enrollment
        )

    def test_plan_assignment_creates_student_account(self):
        plan = self.create_plan()
        account = self.assign_plan(plan)

        self.assertEqual(account.plan, plan)

        response = self.owner_client.get(
            f"/api/finance/accounts/?academic_year={self.year.id}",
            **self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            Decimal(response.data[0]["expected_amount"]),
            Decimal("90000.00"),
        )
        self.assertEqual(
            Decimal(response.data[0]["balance"]),
            Decimal("90000.00"),
        )
        self.assertEqual(
            response.data[0]["payment_status"],
            "UNPAID",
        )

    def test_accountant_can_record_payment_and_receipt_pdf(self):
        plan = self.create_plan()
        account = self.assign_plan(plan)

        response = self.accountant_client.post(
            "/api/finance/payments/record/",
            {
                "tuition_account": account.id,
                "amount": "60000.00",
                "method": "MOBILE_MONEY",
                "reference": "OM-123456",
            },
            format="json",
            **self.host,
        )

        self.assertEqual(response.status_code, 201)
        payment_data = response.data["payment"]
        account_data = response.data["account"]

        self.assertTrue(
            payment_data["receipt_number"].startswith("REC-")
        )
        self.assertEqual(
            Decimal(account_data["paid_amount"]),
            Decimal("60000.00"),
        )
        self.assertEqual(
            Decimal(account_data["balance"]),
            Decimal("30000.00"),
        )
        self.assertEqual(
            account_data["payment_status"],
            "PARTIAL",
        )

        payment = TuitionPayment.objects.get()
        allocations = list(
            PaymentAllocation.objects.filter(
                payment=payment
            ).order_by("installment__order")
        )
        self.assertEqual(len(allocations), 2)
        self.assertEqual(
            allocations[0].amount,
            Decimal("50000.00"),
        )
        self.assertEqual(
            allocations[1].amount,
            Decimal("10000.00"),
        )

        receipt = PaymentReceiptSnapshot.objects.get(
            payment=payment
        )
        with receipt.pdf_file.open("rb") as handle:
            self.assertEqual(handle.read(4), b"%PDF")

        download = self.accountant_client.get(
            f"/api/finance/payments/{payment.id}/receipt/",
            **self.host,
        )
        self.assertEqual(download.status_code, 200)
        self.assertEqual(
            download["Content-Type"],
            "application/pdf",
        )

    def test_overpayment_is_rejected(self):
        plan = self.create_plan()
        account = self.assign_plan(plan)

        response = self.accountant_client.post(
            "/api/finance/payments/record/",
            {
                "tuition_account": account.id,
                "amount": "100000.00",
                "method": "CASH",
            },
            format="json",
            **self.host,
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(TuitionPayment.objects.count(), 0)

    def test_plan_structure_is_locked_after_first_payment(self):
        plan = self.create_plan()
        account = self.assign_plan(plan)

        payment = self.accountant_client.post(
            "/api/finance/payments/record/",
            {
                "tuition_account": account.id,
                "amount": "10000.00",
                "method": "CASH",
            },
            format="json",
            **self.host,
        )
        self.assertEqual(payment.status_code, 201)

        installment = plan.installments.first()
        edit = self.owner_client.patch(
            f"/api/finance/installments/{installment.id}/",
            {
                "amount": "60000.00",
            },
            format="json",
            **self.host,
        )
        self.assertEqual(edit.status_code, 409)

    def test_dashboard_totals(self):
        plan = self.create_plan()
        account = self.assign_plan(plan)

        payment = self.accountant_client.post(
            "/api/finance/payments/record/",
            {
                "tuition_account": account.id,
                "amount": "30000.00",
                "method": "CASH",
            },
            format="json",
            **self.host,
        )
        self.assertEqual(payment.status_code, 201)

        response = self.owner_client.get(
            (
                "/api/finance/dashboard/"
                f"?academic_year={self.year.id}"
            ),
            **self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Decimal(response.data["expected_total"]),
            Decimal("90000.00"),
        )
        self.assertEqual(
            Decimal(response.data["collected_total"]),
            Decimal("30000.00"),
        )
        self.assertEqual(
            Decimal(response.data["outstanding_total"]),
            Decimal("60000.00"),
        )
        self.assertEqual(response.data["partial_count"], 1)

    def test_teacher_cannot_access_finance(self):
        teacher = User.objects.create_user(
            email="finance-teacher@example.com",
            password="Password123!",
        )
        SchoolMembership.objects.create(
            school=self.school,
            user=teacher,
            role=SchoolMembership.Role.TEACHER,
        )

        client = APIClient()
        client.force_authenticate(user=teacher)

        response = client.get(
            "/api/finance/dashboard/",
            **self.host,
        )
        self.assertEqual(response.status_code, 403)
