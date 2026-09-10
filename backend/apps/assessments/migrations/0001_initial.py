from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("academics", "0002_curriculum_periods_rules"),
        ("people", "0001_initial"),
        ("teaching", "0001_initial"),
        ("tenants", "0002_school_branding"),
    ]
    operations = [
        migrations.CreateModel(
            name="AssessmentPeriodControl",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score_entry_open", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academic_period", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="assessment_control", to="academics.academicperiod")),
                ("opened_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="opened_assessment_periods", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assessment_period_controls", to="tenants.school")),
            ],
        ),
        migrations.CreateModel(
            name="Assessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("kind", models.CharField(choices=[("QUIZ", "Interrogation"), ("TEST", "Devoir / contrôle"), ("HOMEWORK", "Travail à domicile"), ("EXAM", "Examen"), ("ORAL", "Oral"), ("PRACTICAL", "Pratique"), ("OTHER", "Autre")], default="TEST", max_length=20)),
                ("assessment_date", models.DateField(blank=True, null=True)),
                ("max_score", models.DecimalField(decimal_places=2, default=20, max_digits=7)),
                ("weight", models.DecimalField(decimal_places=3, default=1, max_digits=7)),
                ("instructions", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("DRAFT", "Brouillon"), ("INPUT", "Saisie en cours"), ("SUBMITTED", "Soumis"), ("VALIDATED", "Validé"), ("PUBLISHED", "Publié")], default="DRAFT", max_length=20)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("reopened_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academic_period", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assessments", to="academics.academicperiod")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_assessments", to=settings.AUTH_USER_MODEL)),
                ("published_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="published_assessments", to=settings.AUTH_USER_MODEL)),
                ("reopened_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reopened_assessments", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assessments", to="tenants.school")),
                ("teaching_assignment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assessments", to="teaching.teachingassignment")),
                ("validated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="validated_assessments", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Grade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.DecimalField(blank=True, decimal_places=3, max_digits=7, null=True)),
                ("is_absent", models.BooleanField(default=False)),
                ("is_exempt", models.BooleanField(default=False)),
                ("comment", models.CharField(blank=True, max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assessment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grades", to="assessments.assessment")),
                ("enrollment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="grades", to="people.enrollment")),
                ("entered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="entered_grades", to=settings.AUTH_USER_MODEL)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grades", to="tenants.school")),
            ],
        ),
        migrations.AddConstraint(
            model_name="assessment",
            constraint=models.UniqueConstraint(fields=("school", "teaching_assignment", "academic_period", "title"), name="unique_assessment_title_per_assignment_period"),
        ),
        migrations.AddConstraint(
            model_name="grade",
            constraint=models.UniqueConstraint(fields=("school", "assessment", "enrollment"), name="unique_grade_per_assessment_enrollment"),
        ),
    ]
