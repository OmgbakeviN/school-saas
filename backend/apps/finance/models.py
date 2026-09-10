from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def receipt_pdf_upload_to(instance, filename):
    return (
        f"finance/receipts/{instance.school_id}/"
        f"{instance.payment.tuition_account.enrollment.academic_year_id}/"
        f"{filename}"
    )


class TuitionPlan(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="tuition_plans",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="tuition_plans",
    )
    name = models.CharField(max_length=160)
    currency = models.CharField(max_length=10, default="XAF")
    level = models.ForeignKey(
        "academics.Level",
        on_delete=models.PROTECT,
        related_name="tuition_plans",
        null=True,
        blank=True,
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        on_delete=models.PROTECT,
        related_name="tuition_plans",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-academic_year__start_date", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "academic_year", "name"),
                name="unique_tuition_plan_name_per_year",
            ),
        ]

    def clean(self):
        errors = {}

        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            errors["academic_year"] = "L'année scolaire n'appartient pas à cet établissement."

        if self.level_id and self.level.school_id != self.school_id:
            errors["level"] = "Le niveau n'appartient pas à cet établissement."

        if self.classroom_id:
            if self.classroom.school_id != self.school_id:
                errors["classroom"] = "La classe n'appartient pas à cet établissement."
            if (
                self.academic_year_id
                and self.classroom.academic_year_id != self.academic_year_id
            ):
                errors["classroom"] = (
                    "La classe doit appartenir à l'année scolaire du plan."
                )

        if self.level_id and self.classroom_id:
            errors["classroom"] = (
                "Choisissez soit un niveau, soit une classe, pas les deux."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class TuitionInstallment(models.Model):
    plan = models.ForeignKey(
        TuitionPlan,
        on_delete=models.CASCADE,
        related_name="installments",
    )
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "due_date", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("plan", "order"),
                name="unique_installment_order_per_plan",
            ),
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({
                "amount": "Le montant doit être supérieur à zéro."
            })

    def __str__(self):
        return f"{self.plan.name} - {self.name}"


class StudentTuitionAccount(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="tuition_accounts",
    )
    enrollment = models.OneToOneField(
        "people.Enrollment",
        on_delete=models.PROTECT,
        related_name="tuition_account",
    )
    plan = models.ForeignKey(
        TuitionPlan,
        on_delete=models.PROTECT,
        related_name="student_accounts",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = (
            "enrollment__classroom__name",
            "enrollment__student__last_name",
        )

    def clean(self):
        errors = {}

        if self.enrollment_id:
            if self.enrollment.school_id != self.school_id:
                errors["enrollment"] = "L'inscription n'appartient pas à cet établissement."
            if (
                self.plan_id
                and self.enrollment.academic_year_id != self.plan.academic_year_id
            ):
                errors["plan"] = (
                    "Le plan de pension doit appartenir à l'année de l'inscription."
                )

        if self.plan_id and self.plan.school_id != self.school_id:
            errors["plan"] = "Le plan n'appartient pas à cet établissement."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.enrollment.student} - {self.plan.name}"


class TuitionPayment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Espèces"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
        BANK_TRANSFER = "BANK_TRANSFER", "Virement bancaire"
        CARD = "CARD", "Carte"
        OTHER = "OTHER", "Autre"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.PROTECT,
        related_name="tuition_payments",
    )
    tuition_account = models.ForeignKey(
        StudentTuitionAccount,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(
        max_length=30,
        choices=Method.choices,
        default=Method.CASH,
    )
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField()
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_tuition_payments",
    )
    receipt_number = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-paid_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "receipt_number"),
                condition=~models.Q(receipt_number=""),
                name="unique_receipt_number_per_school",
            ),
        ]

    def clean(self):
        errors = {}

        if self.amount <= 0:
            errors["amount"] = "Le montant doit être supérieur à zéro."

        if (
            self.tuition_account_id
            and self.tuition_account.school_id != self.school_id
        ):
            errors["tuition_account"] = (
                "Le compte de pension n'appartient pas à cet établissement."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.receipt_number or f"Paiement #{self.pk or 'nouveau'}"


class PaymentAllocation(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.PROTECT,
        related_name="payment_allocations",
    )
    payment = models.ForeignKey(
        TuitionPayment,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    installment = models.ForeignKey(
        TuitionInstallment,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ("installment__order",)
        constraints = [
            models.UniqueConstraint(
                fields=("payment", "installment"),
                name="unique_installment_allocation_per_payment",
            ),
        ]

    def clean(self):
        errors = {}

        if self.amount <= 0:
            errors["amount"] = "Le montant alloué doit être positif."

        if self.payment_id and self.payment.school_id != self.school_id:
            errors["payment"] = "Le paiement n'appartient pas à cet établissement."

        if self.installment_id:
            if (
                self.payment_id
                and self.installment.plan_id
                != self.payment.tuition_account.plan_id
            ):
                errors["installment"] = (
                    "La tranche doit appartenir au plan de pension de l'élève."
                )

        if errors:
            raise ValidationError(errors)


class PaymentReceiptSnapshot(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.PROTECT,
        related_name="payment_receipts",
    )
    payment = models.OneToOneField(
        TuitionPayment,
        on_delete=models.PROTECT,
        related_name="receipt",
    )
    payload = models.JSONField()
    payload_sha256 = models.CharField(max_length=64)
    pdf_file = models.FileField(
        upload_to=receipt_pdf_upload_to,
        max_length=500,
    )
    pdf_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(
                "Un reçu de paiement est immuable après sa création."
            )
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.payment.receipt_number
