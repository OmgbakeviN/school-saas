# Generated for BE WISE School STEP 04.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("academics", "0002_curriculum_periods_rules"),
        ("people", "0001_initial"),
        ("tenants", "0002_school_branding"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeachingAssignment",
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
                ("can_enter_scores", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teaching_assignments",
                        to="academics.academicyear",
                    ),
                ),
                (
                    "classroom",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teaching_assignments",
                        to="academics.classroom",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teaching_assignments",
                        to="tenants.school",
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teaching_assignments",
                        to="academics.subject",
                    ),
                ),
                (
                    "teacher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teaching_assignments",
                        to="people.teacher",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "-academic_year__start_date",
                    "classroom__level__order",
                    "classroom__name",
                    "subject__name",
                    "teacher__last_name",
                ),
            },
        ),
        migrations.CreateModel(
            name="ClassroomLeadership",
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
                    "role",
                    models.CharField(
                        choices=[
                            ("CLASS_TEACHER", "Titulaire de classe"),
                            ("HOMEROOM_TEACHER", "Professeur principal"),
                        ],
                        max_length=30,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="classroom_leaderships",
                        to="academics.academicyear",
                    ),
                ),
                (
                    "classroom",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="leaderships",
                        to="academics.classroom",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="classroom_leaderships",
                        to="tenants.school",
                    ),
                ),
                (
                    "teacher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="classroom_leaderships",
                        to="people.teacher",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "-academic_year__start_date",
                    "classroom__level__order",
                    "classroom__name",
                    "role",
                ),
            },
        ),
        migrations.AddConstraint(
            model_name="teachingassignment",
            constraint=models.UniqueConstraint(
                fields=(
                    "school",
                    "academic_year",
                    "teacher",
                    "subject",
                    "classroom",
                ),
                name="unique_teaching_assignment",
            ),
        ),
        migrations.AddConstraint(
            model_name="classroomleadership",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=("school", "academic_year", "classroom", "role"),
                name="unique_active_classroom_leadership_role",
            ),
        ),
    ]
