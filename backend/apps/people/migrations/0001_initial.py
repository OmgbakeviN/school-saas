from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("academics", "0002_curriculum_periods_rules"),
        ("tenants", "0002_school_branding"),
    ]

    operations = [
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("matricule", models.CharField(max_length=60)),
                ("first_name", models.CharField(max_length=120)),
                ("last_name", models.CharField(max_length=120)),
                ("gender", models.CharField(blank=True, choices=[("MALE", "Masculin"), ("FEMALE", "Féminin"), ("OTHER", "Autre")], max_length=10)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("place_of_birth", models.CharField(blank=True, max_length=160)),
                ("nationality", models.CharField(blank=True, max_length=100)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("admission_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("ACTIVE", "Actif"), ("INACTIVE", "Inactif"), ("GRADUATED", "Diplômé"), ("TRANSFERRED", "Transféré"), ("WITHDRAWN", "Retiré")], default="ACTIVE", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="students", to="tenants.school")),
            ],
            options={"ordering": ("last_name", "first_name")},
        ),
        migrations.CreateModel(
            name="Teacher",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("employee_number", models.CharField(max_length=60)),
                ("first_name", models.CharField(max_length=120)),
                ("last_name", models.CharField(max_length=120)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("speciality", models.CharField(blank=True, max_length=160)),
                ("hire_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("ACTIVE", "Actif"), ("INACTIVE", "Inactif")], default="ACTIVE", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="teachers", to="tenants.school")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teacher_profiles", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("last_name", "first_name")},
        ),
        migrations.CreateModel(
            name="Guardian",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=120)),
                ("last_name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=40)),
                ("alternate_phone", models.CharField(blank=True, max_length=40)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("occupation", models.CharField(blank=True, max_length=160)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("preferred_language", models.CharField(choices=[("FR", "Français"), ("EN", "English")], default="FR", max_length=10)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guardians", to="tenants.school")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="guardian_profiles", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("last_name", "first_name")},
        ),
        migrations.CreateModel(
            name="StudentGuardian",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("relationship", models.CharField(choices=[("FATHER", "Père"), ("MOTHER", "Mère"), ("GUARDIAN", "Tuteur / tutrice"), ("SIBLING", "Frère / sœur"), ("OTHER", "Autre")], default="GUARDIAN", max_length=20)),
                ("is_primary", models.BooleanField(default=False)),
                ("receives_notifications", models.BooleanField(default=True)),
                ("can_receive_results", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("guardian", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_links", to="people.guardian")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_guardian_links", to="tenants.school")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guardian_links", to="people.student")),
            ],
            options={"ordering": ("student__last_name", "student__first_name")},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enrollment_date", models.DateField(blank=True, null=True)),
                ("roll_number", models.CharField(blank=True, max_length=40)),
                ("status", models.CharField(choices=[("ACTIVE", "Inscrit"), ("COMPLETED", "Année terminée"), ("TRANSFERRED", "Transféré"), ("WITHDRAWN", "Retiré")], default="ACTIVE", max_length=20)),
                ("final_average", models.DecimalField(blank=True, decimal_places=3, max_digits=7, null=True)),
                ("promotion_decision", models.CharField(choices=[("PENDING", "En attente"), ("PROMOTED", "Admis / promu"), ("REPEATED", "Redouble"), ("GRADUATED", "Diplômé"), ("TRANSFERRED", "Transféré"), ("WITHDRAWN", "Retiré")], default="PENDING", max_length=20)),
                ("decision_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academic_year", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="academics.academicyear")),
                ("classroom", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="academics.classroom")),
                ("next_enrollment", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="previous_enrollment", to="people.enrollment")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="tenants.school")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="people.student")),
            ],
            options={"ordering": ("-academic_year__start_date", "classroom__name", "student__last_name")},
        ),
        migrations.AddConstraint(
            model_name="student",
            constraint=models.UniqueConstraint(fields=("school", "matricule"), name="unique_student_matricule_per_school"),
        ),
        migrations.AddConstraint(
            model_name="teacher",
            constraint=models.UniqueConstraint(fields=("school", "employee_number"), name="unique_teacher_number_per_school"),
        ),
        migrations.AddConstraint(
            model_name="teacher",
            constraint=models.UniqueConstraint(condition=models.Q(user__isnull=False), fields=("school", "user"), name="unique_teacher_user_per_school"),
        ),
        migrations.AddConstraint(
            model_name="studentguardian",
            constraint=models.UniqueConstraint(fields=("school", "student", "guardian"), name="unique_guardian_link_per_student"),
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(fields=("school", "student", "academic_year"), name="unique_student_enrollment_per_year"),
        ),
    ]
