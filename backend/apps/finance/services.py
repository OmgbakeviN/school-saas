import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.people.models import Enrollment

from .models import (
    PaymentAllocation,
    PaymentReceiptSnapshot,
    StudentTuitionAccount,
    TuitionPayment,
    TuitionPlan,
)
from .pdf import generate_payment_receipt_pdf


MONEY = Decimal("0.01")


def money(value):
    return Decimal(value or 0).quantize(
        MONEY,
        rounding=ROUND_HALF_UP,
    )


def plan_total(plan):
    value = (
        plan.installments
        .filter(is_active=True)
        .aggregate(total=Sum("amount"))
        .get("total")
    )
    return money(value)


def account_paid(account):
    value = (
        account.payments
        .aggregate(total=Sum("amount"))
        .get("total")
    )
    return money(value)


def account_summary(account):
    expected = plan_total(account.plan)
    paid = account_paid(account)
    balance = max(Decimal("0"), expected - paid)

    if expected > 0 and balance == 0:
        status = "PAID"
    elif paid > 0:
        status = "PARTIAL"
    else:
        status = "UNPAID"

    installment_rows = []
    for installment in account.plan.installments.filter(
        is_active=True
    ).order_by("order", "due_date", "id"):
        allocated = (
            PaymentAllocation.objects
            .filter(
                payment__tuition_account=account,
                installment=installment,
            )
            .aggregate(total=Sum("amount"))
            .get("total")
        )
        allocated = money(allocated)
        remaining = max(
            Decimal("0"),
            money(installment.amount) - allocated,
        )

        installment_rows.append({
            "id": installment.id,
            "name": installment.name,
            "amount": money(installment.amount),
            "paid": allocated,
            "remaining": remaining,
            "due_date": installment.due_date,
            "order": installment.order,
            "is_paid": remaining == 0,
        })

    return {
        "expected_amount": expected,
        "paid_amount": paid,
        "balance": balance,
        "payment_status": status,
        "installments": installment_rows,
    }


def enrich_account(account):
    summary = account_summary(account)
    for key, value in summary.items():
        setattr(account, key, value)
    return account


def eligible_enrollments_for_plan(plan):
    queryset = Enrollment.objects.filter(
        school=plan.school,
        academic_year=plan.academic_year,
        status=Enrollment.Status.ACTIVE,
    )

    if plan.classroom_id:
        queryset = queryset.filter(
            classroom=plan.classroom,
        )
    elif plan.level_id:
        queryset = queryset.filter(
            classroom__level=plan.level,
        )

    return queryset.select_related(
        "student",
        "academic_year",
        "classroom",
        "classroom__level",
    )


@transaction.atomic
def assign_plan_to_eligible_students(plan):
    created = 0
    updated = 0
    unchanged = 0
    conflicts = []

    for enrollment in eligible_enrollments_for_plan(plan):
        account = StudentTuitionAccount.objects.filter(
            enrollment=enrollment,
        ).first()

        if account:
            if account.plan_id == plan.id:
                unchanged += 1
                continue

            if account.payments.exists():
                conflicts.append({
                    "enrollment": enrollment.id,
                    "student": str(enrollment.student),
                    "detail": (
                        "Un autre plan est déjà utilisé et possède des paiements."
                    ),
                })
                continue

            account.plan = plan
            account.school = plan.school
            account.full_clean()
            account.save(update_fields=["plan", "school"])
            updated += 1
            continue

        account = StudentTuitionAccount(
            school=plan.school,
            enrollment=enrollment,
            plan=plan,
        )
        account.full_clean()
        account.save()
        created += 1

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "conflicts": conflicts,
    }


def next_receipt_number(payment):
    year = payment.paid_at.year
    return f"REC-{year}-{payment.id:07d}"


def canonical_hash(payload):
    raw = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def display_user(user):
    name = user.get_full_name().strip()
    return name or user.email


def build_receipt_payload(payment):
    account = payment.tuition_account
    enrollment = account.enrollment
    school = payment.school
    summary = account_summary(account)

    allocations = [
        {
            "name": allocation.installment.name,
            "amount": money(allocation.amount),
        }
        for allocation in payment.allocations.select_related(
            "installment"
        ).order_by("installment__order")
    ]

    payload = {
        "schema_version": 1,
        "receipt_number": payment.receipt_number,
        "school": {
            "id": school.id,
            "name": school.name,
            "acronym": school.acronym,
            "motto": school.motto,
            "city": school.city,
            "country": school.country,
            "phone": school.phone,
            "email": school.email,
            "primary_color": school.primary_color,
            "secondary_color": school.secondary_color,
        },
        "student": {
            "id": enrollment.student_id,
            "name": (
                f"{enrollment.student.last_name} "
                f"{enrollment.student.first_name}"
            ).strip(),
            "matricule": enrollment.student.matricule,
        },
        "academic": {
            "academic_year": enrollment.academic_year.name,
            "classroom": enrollment.classroom.name,
            "level": enrollment.classroom.level.name,
        },
        "plan": {
            "id": account.plan_id,
            "name": account.plan.name,
            "currency": account.plan.currency,
        },
        "payment": {
            "id": payment.id,
            "amount": money(payment.amount),
            "method": payment.method,
            "method_label": payment.get_method_display(),
            "reference": payment.reference,
            "notes": payment.notes,
        },
        "allocations": allocations,
        "balance": {
            "expected": summary["expected_amount"],
            "paid_after": summary["paid_amount"],
            "remaining_after": summary["balance"],
        },
        "paid_at": payment.paid_at.isoformat(),
        "paid_at_display": timezone.localtime(
            payment.paid_at
        ).strftime("%d/%m/%Y %H:%M"),
        "received_by": display_user(payment.received_by),
        "fingerprint": "",
    }

    fingerprint = canonical_hash(payload)
    payload["fingerprint"] = fingerprint[:16].upper()
    return json_safe(payload)


@transaction.atomic
def record_payment(
    *,
    school,
    account_id,
    amount,
    method,
    received_by,
    reference="",
    notes="",
    paid_at=None,
):
    account = (
        StudentTuitionAccount.objects
        .select_for_update()
        .select_related(
            "plan",
            "enrollment__student",
            "enrollment__academic_year",
            "enrollment__classroom__level",
        )
        .get(
            school=school,
            id=account_id,
        )
    )

    amount = money(amount)
    if amount <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")

    summary_before = account_summary(account)
    if summary_before["expected_amount"] <= 0:
        raise ValueError(
            "Le plan de pension ne contient aucune tranche active."
        )

    if summary_before["balance"] <= 0:
        raise ValueError("La pension de cet élève est déjà soldée.")

    if amount > summary_before["balance"]:
        raise ValueError(
            "Le paiement dépasse le reste à payer."
        )

    payment = TuitionPayment(
        school=school,
        tuition_account=account,
        amount=amount,
        method=method,
        reference=reference,
        notes=notes,
        paid_at=paid_at or timezone.now(),
        received_by=received_by,
    )
    payment.full_clean()
    payment.save()

    payment.receipt_number = next_receipt_number(payment)
    payment.save(update_fields=["receipt_number"])

    remaining_payment = amount

    for installment in account.plan.installments.filter(
        is_active=True
    ).order_by("order", "due_date", "id"):
        previous_allocated = (
            PaymentAllocation.objects
            .filter(
                payment__tuition_account=account,
                installment=installment,
            )
            .aggregate(total=Sum("amount"))
            .get("total")
        )
        previous_allocated = money(previous_allocated)
        installment_remaining = max(
            Decimal("0"),
            money(installment.amount) - previous_allocated,
        )

        if installment_remaining <= 0:
            continue

        allocated = min(
            remaining_payment,
            installment_remaining,
        )
        if allocated <= 0:
            break

        allocation = PaymentAllocation(
            school=school,
            payment=payment,
            installment=installment,
            amount=allocated,
        )
        allocation.full_clean()
        allocation.save()

        remaining_payment -= allocated
        if remaining_payment <= 0:
            break

    payload = build_receipt_payload(payment)
    payload_hash = canonical_hash(payload)

    logo_path = None
    try:
        if school.logo:
            logo_path = school.logo.path
    except Exception:
        logo_path = None

    pdf_bytes = generate_payment_receipt_pdf(
        payload=payload,
        logo_path=logo_path,
    )
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    receipt = PaymentReceiptSnapshot(
        school=school,
        payment=payment,
        payload=payload,
        payload_sha256=payload_hash,
        pdf_sha256=pdf_hash,
    )
    filename = f"{payment.receipt_number}.pdf"
    receipt.pdf_file.save(
        filename,
        ContentFile(pdf_bytes),
        save=False,
    )
    receipt.save()

    enrich_account(account)
    return payment, account


def dashboard_summary(*, school, academic_year_id=None, classroom_id=None):
    accounts = StudentTuitionAccount.objects.filter(
        school=school,
    ).select_related(
        "plan",
        "enrollment__academic_year",
        "enrollment__classroom",
    ).prefetch_related(
        "plan__installments",
        "payments",
    )

    if academic_year_id:
        accounts = accounts.filter(
            enrollment__academic_year_id=academic_year_id,
        )

    if classroom_id:
        accounts = accounts.filter(
            enrollment__classroom_id=classroom_id,
        )

    expected_total = Decimal("0")
    collected_total = Decimal("0")
    paid_count = 0
    partial_count = 0
    unpaid_count = 0

    for account in accounts:
        summary = account_summary(account)
        expected_total += summary["expected_amount"]
        collected_total += summary["paid_amount"]

        if summary["payment_status"] == "PAID":
            paid_count += 1
        elif summary["payment_status"] == "PARTIAL":
            partial_count += 1
        else:
            unpaid_count += 1

    outstanding = max(
        Decimal("0"),
        expected_total - collected_total,
    )

    if expected_total > 0:
        rate = (
            collected_total
            / expected_total
            * Decimal("100")
        ).quantize(Decimal("0.01"))
    else:
        rate = Decimal("0")

    today = timezone.localdate()
    payments_today = TuitionPayment.objects.filter(
        school=school,
        paid_at__date=today,
    )

    if academic_year_id:
        payments_today = payments_today.filter(
            tuition_account__enrollment__academic_year_id=academic_year_id,
        )
    if classroom_id:
        payments_today = payments_today.filter(
            tuition_account__enrollment__classroom_id=classroom_id,
        )

    today_total = money(
        payments_today.aggregate(total=Sum("amount")).get("total")
    )

    return {
        "academic_year": (
            int(academic_year_id)
            if academic_year_id
            else None
        ),
        "expected_total": money(expected_total),
        "collected_total": money(collected_total),
        "outstanding_total": money(outstanding),
        "collection_rate": rate,
        "accounts_count": accounts.count(),
        "paid_count": paid_count,
        "partial_count": partial_count,
        "unpaid_count": unpaid_count,
        "payments_today": today_total,
    }
