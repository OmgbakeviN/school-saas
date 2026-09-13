from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0002_curriculum_periods_rules"),
        ("report_cards", "0001_initial"),
        ("tenants", "0002_school_branding"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportCardTemplate",
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
                ("name", models.CharField(max_length=120)),
                (
                    "template_key",
                    models.CharField(
                        choices=[
                            ("CLASSIC", "Classique"),
                            ("MODERN", "Moderne"),
                            ("COMPACT", "Compact"),
                            (
                                "SECONDARY_LANDSCAPE",
                                "Secondaire paysage",
                            ),
                        ],
                        default="CLASSIC",
                        max_length=40,
                    ),
                ),
                ("version", models.PositiveIntegerField(default=1)),
                ("is_default", models.BooleanField(default=False)),
                ("show_rank", models.BooleanField(default=True)),
                (
                    "show_class_average",
                    models.BooleanField(default=True),
                ),
                ("show_effective", models.BooleanField(default=True)),
                ("show_decision", models.BooleanField(default=True)),
                (
                    "show_subject_comments",
                    models.BooleanField(default=True),
                ),
                (
                    "show_teacher_comment",
                    models.BooleanField(default=True),
                ),
                (
                    "show_direction_comment",
                    models.BooleanField(default=True),
                ),
                ("show_qr", models.BooleanField(default=True)),
                (
                    "font_scale",
                    models.DecimalField(
                        decimal_places=2,
                        default="1.00",
                        help_text="Échelle entre 0.80 et 1.10.",
                        max_digits=3,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "cycle",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "Vide = modèle valable pour tous les cycles "
                            "de l'établissement."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="report_card_templates",
                        to="academics.cycle",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="report_card_templates",
                        to="tenants.school",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "cycle__order",
                    "-is_default",
                    "name",
                ),
            },
        ),
        migrations.AddConstraint(
            model_name="reportcardtemplate",
            constraint=models.UniqueConstraint(
                fields=("school", "cycle", "name"),
                name="unique_report_card_template_name_per_scope",
            ),
        ),
    ]
