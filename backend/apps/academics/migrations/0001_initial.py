from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenants", "0002_school_branding"),
    ]

    operations = [
        migrations.CreateModel(
            name="AcademicYear",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=30)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("period_system", models.CharField(choices=[("TRIMESTER", "Trimestres"), ("SEMESTER", "Semestres"), ("CUSTOM", "Personnalisé")], default="TRIMESTER", max_length=20)),
                ("is_active", models.BooleanField(default=False)),
                ("is_closed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="academic_years", to="tenants.school")),
            ],
            options={"ordering": ("-start_date",)},
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("code", models.SlugField(max_length=30)),
                ("language", models.CharField(choices=[("FRENCH", "Francophone"), ("ENGLISH", "Anglophone"), ("BILINGUAL", "Bilingue")], default="FRENCH", max_length=20)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="academic_sections", to="tenants.school")),
            ],
            options={"ordering": ("order", "name")},
        ),
        migrations.CreateModel(
            name="Cycle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("code", models.SlugField(max_length=40)),
                ("kind", models.CharField(choices=[("PRIMARY", "Primaire"), ("SECONDARY", "Secondaire"), ("OTHER", "Autre")], default="SECONDARY", max_length=20)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="academic_cycles", to="tenants.school")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cycles", to="academics.section")),
            ],
            options={"ordering": ("section__order", "order", "name")},
        ),
        migrations.CreateModel(
            name="Level",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("code", models.SlugField(max_length=40)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("cycle", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="levels", to="academics.cycle")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="academic_levels", to="tenants.school")),
            ],
            options={"ordering": ("cycle__order", "order", "name")},
        ),
        migrations.CreateModel(
            name="Classroom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("code", models.SlugField(max_length=50)),
                ("capacity", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="classrooms", to="academics.academicyear")),
                ("level", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="classrooms", to="academics.level")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="classrooms", to="tenants.school")),
            ],
            options={"ordering": ("level__order", "order", "name")},
        ),
        migrations.AddConstraint(
            model_name="academicyear",
            constraint=models.UniqueConstraint(fields=("school", "name"), name="unique_academic_year_name_per_school"),
        ),
        migrations.AddConstraint(
            model_name="academicyear",
            constraint=models.UniqueConstraint(condition=Q(("is_active", True)), fields=("school",), name="unique_active_academic_year_per_school"),
        ),
        migrations.AddConstraint(
            model_name="section",
            constraint=models.UniqueConstraint(fields=("school", "code"), name="unique_section_code_per_school"),
        ),
        migrations.AddConstraint(
            model_name="cycle",
            constraint=models.UniqueConstraint(fields=("school", "code"), name="unique_cycle_code_per_school"),
        ),
        migrations.AddConstraint(
            model_name="level",
            constraint=models.UniqueConstraint(fields=("school", "cycle", "code"), name="unique_level_code_per_cycle"),
        ),
        migrations.AddConstraint(
            model_name="classroom",
            constraint=models.UniqueConstraint(fields=("school", "academic_year", "code"), name="unique_classroom_code_per_year"),
        ),
    ]
