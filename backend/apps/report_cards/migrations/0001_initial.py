import apps.report_cards.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("people", "0001_initial"),
        ("academics", "0002_curriculum_periods_rules"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportCardSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "report_type",
                    models.CharField(
                        choices=[
                            ("PERIOD", "Bulletin de période"),
                            ("ANNUAL", "Bulletin annuel"),
                        ],
                        max_length=20,
                    ),
                ),
                ("version", models.PositiveIntegerField()),
                ("payload", models.JSONField()),
                ("payload_sha256", models.CharField(max_length=64)),
                (
                    "verification_token",
                    models.CharField(
                        default=apps.report_cards.models.generate_verification_token,
                        editable=False,
                        max_length=80,
                        unique=True,
                    ),
                ),
                (
                    "pdf_file",
                    models.FileField(
                        max_length=500,
                        upload_to=apps.report_cards.models.report_card_pdf_upload_to,
                    ),
                ),
                ("pdf_sha256", models.CharField(max_length=64)),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                (
                    "academic_period",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_card_snapshots",
                        to="academics.academicperiod",
                    ),
                ),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_card_snapshots",
                        to="academics.academicyear",
                    ),
                ),
                (
                    "enrollment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_card_snapshots",
                        to="people.enrollment",
                    ),
                ),
                (
                    "published_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_report_cards",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_card_snapshots",
                        to="tenants.school",
                    ),
                ),
                (
                    "supersedes",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="newer_versions",
                        to="report_cards.reportcardsnapshot",
                    ),
                ),
            ],
            options={
                "ordering": ("-published_at", "-version"),
            },
        ),
        migrations.AddConstraint(
            model_name="reportcardsnapshot",
            constraint=models.UniqueConstraint(
                condition=models.Q(("report_type", "PERIOD")),
                fields=(
                    "school",
                    "enrollment",
                    "report_type",
                    "academic_period",
                    "version",
                ),
                name="unique_period_report_card_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="reportcardsnapshot",
            constraint=models.UniqueConstraint(
                condition=models.Q(("report_type", "ANNUAL")),
                fields=(
                    "school",
                    "enrollment",
                    "report_type",
                    "academic_year",
                    "version",
                ),
                name="unique_annual_report_card_version",
            ),
        ),
    ]
