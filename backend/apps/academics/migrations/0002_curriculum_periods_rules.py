from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cycle",
            name="max_score_override",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="cycle",
            name="promotion_threshold_override",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="level",
            name="max_score_override",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="level",
            name="promotion_threshold_override",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="AcademicPolicy",
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
                    "default_max_score",
                    models.DecimalField(
                        decimal_places=2,
                        default=20,
                        max_digits=7,
                    ),
                ),
                (
                    "default_promotion_threshold",
                    models.DecimalField(
                        decimal_places=2,
                        default=10,
                        max_digits=7,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "school",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academic_policy",
                        to="tenants.school",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AcademicPeriod",
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
                ("name", models.CharField(max_length=100)),
                ("code", models.SlugField(max_length=40)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("TRIMESTER", "Trimestre"),
                            ("SEMESTER", "Semestre"),
                            ("CUSTOM", "Personnalisé"),
                        ],
                        default="TRIMESTER",
                        max_length=20,
                    ),
                ),
                ("order", models.PositiveSmallIntegerField(default=1)),
                (
                    "weight",
                    models.DecimalField(
                        decimal_places=3,
                        default=1,
                        max_digits=7,
                    ),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="periods",
                        to="academics.academicyear",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academic_periods",
                        to="tenants.school",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "academic_year__start_date",
                    "order",
                    "name",
                ),
            },
        ),
        migrations.CreateModel(
            name="Subject",
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
                ("code", models.SlugField(max_length=50)),
                ("category", models.CharField(blank=True, max_length=80)),
                (
                    "default_teaching_language",
                    models.CharField(
                        choices=[
                            ("DEFAULT", "Langue de la section"),
                            ("FRENCH", "Français"),
                            ("ENGLISH", "Anglais"),
                            ("BILINGUAL", "Bilingue"),
                        ],
                        default="DEFAULT",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subjects",
                        to="tenants.school",
                    ),
                ),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="LevelSubject",
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
                    "coefficient",
                    models.DecimalField(
                        decimal_places=3,
                        default=1,
                        max_digits=7,
                    ),
                ),
                (
                    "max_score_override",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=7,
                        null=True,
                    ),
                ),
                (
                    "teaching_language",
                    models.CharField(
                        choices=[
                            ("DEFAULT", "Langue de la section"),
                            ("FRENCH", "Français"),
                            ("ENGLISH", "Anglais"),
                            ("BILINGUAL", "Bilingue"),
                        ],
                        default="DEFAULT",
                        max_length=20,
                    ),
                ),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "level",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subject_configs",
                        to="academics.level",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="level_subjects",
                        to="tenants.school",
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="level_configs",
                        to="academics.subject",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "level__order",
                    "order",
                    "subject__name",
                ),
            },
        ),
        migrations.AddConstraint(
            model_name="academicperiod",
            constraint=models.UniqueConstraint(
                fields=("school", "academic_year", "code"),
                name="unique_period_code_per_year",
            ),
        ),
        migrations.AddConstraint(
            model_name="subject",
            constraint=models.UniqueConstraint(
                fields=("school", "code"),
                name="unique_subject_code_per_school",
            ),
        ),
        migrations.AddConstraint(
            model_name="levelsubject",
            constraint=models.UniqueConstraint(
                fields=("school", "level", "subject"),
                name="unique_subject_per_level",
            ),
        ),
    ]
