from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import apps.finance.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("academics", "0002_curriculum_periods_rules"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TuitionPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("currency", models.CharField(default="XAF", max_length=10)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tuition_plans", to="academics.academicyear")),
                ("classroom", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="tuition_plans", to="academics.classroom")),
                ("level", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="tuition_plans", to="academics.level")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tuition_plans", to="tenants.school")),
            ],
            options={"ordering": ("-academic_year__start_date", "name")},
        ),
        migrations.AddConstraint(
            model_name="tuitionplan",
            constraint=models.UniqueConstraint(
                fields=("school", "academic_year", "name"),
                name="unique_tuition_plan_name_per_year",
            ),
        ),
        migrations.CreateModel(
            name="TuitionInstallment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="installments", to="finance.tuitionplan")),
            ],
            options={"ordering": ("order", "due_date", "id")},
        ),
        migrations.AddConstraint(
            model_name="tuitioninstallment",
            constraint=models.UniqueConstraint(
                fields=("plan", "order"),
                name="unique_installment_order_per_plan",
            ),
        ),
        migrations.CreateModel(
            name="StudentTuitionAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("enrollment", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="tuition_account", to="people.enrollment")),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="student_accounts", to="finance.tuitionplan")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tuition_accounts", to="tenants.school")),
            ],
            options={"ordering": ("enrollment__classroom__name", "enrollment__student__last_name")},
        ),
        migrations.CreateModel(
            name="TuitionPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("method", models.CharField(choices=[("CASH", "Espèces"), ("MOBILE_MONEY", "Mobile Money"), ("BANK_TRANSFER", "Virement bancaire"), ("CARD", "Carte"), ("OTHER", "Autre")], default="CASH", max_length=30)),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("paid_at", models.DateTimeField()),
                ("receipt_number", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("received_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="received_tuition_payments", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tuition_payments", to="tenants.school")),
                ("tuition_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="finance.studenttuitionaccount")),
            ],
            options={"ordering": ("-paid_at", "-id")},
        ),
        migrations.AddConstraint(
            model_name="tuitionpayment",
            constraint=models.UniqueConstraint(
                condition=~models.Q(receipt_number=""),
                fields=("school", "receipt_number"),
                name="unique_receipt_number_per_school",
            ),
        ),
        migrations.CreateModel(
            name="PaymentAllocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("installment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="allocations", to="finance.tuitioninstallment")),
                ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="allocations", to="finance.tuitionpayment")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_allocations", to="tenants.school")),
            ],
            options={"ordering": ("installment__order",)},
        ),
        migrations.AddConstraint(
            model_name="paymentallocation",
            constraint=models.UniqueConstraint(
                fields=("payment", "installment"),
                name="unique_installment_allocation_per_payment",
            ),
        ),
        migrations.CreateModel(
            name="PaymentReceiptSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payload", models.JSONField()),
                ("payload_sha256", models.CharField(max_length=64)),
                ("pdf_file", models.FileField(max_length=500, upload_to=apps.finance.models.receipt_pdf_upload_to)),
                ("pdf_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("payment", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="receipt", to="finance.tuitionpayment")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_receipts", to="tenants.school")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
