from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Masculin"
        FEMALE = "FEMALE", "Féminin"
        OTHER = "OTHER", "Autre"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        INACTIVE = "INACTIVE", "Inactif"
        GRADUATED = "GRADUATED", "Diplômé"
        TRANSFERRED = "TRANSFERRED", "Transféré"
        WITHDRAWN = "WITHDRAWN", "Retiré"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="students",
    )
    matricule = models.CharField(max_length=60)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=160, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    admission_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("last_name", "first_name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "matricule"),
                name="unique_student_matricule_per_school",
            ),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.matricule})"


class Teacher(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        INACTIVE = "INACTIVE", "Inactif"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="teachers",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="teacher_profiles",
        null=True,
        blank=True,
    )
    employee_number = models.CharField(max_length=60)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    speciality = models.CharField(max_length=160, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("last_name", "first_name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "employee_number"),
                name="unique_teacher_number_per_school",
            ),
            models.UniqueConstraint(
                fields=("school", "user"),
                condition=models.Q(user__isnull=False),
                name="unique_teacher_user_per_school",
            ),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Guardian(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="guardians",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="guardian_profiles",
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    alternate_phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=160, blank=True)
    address = models.CharField(max_length=255, blank=True)
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ("FR", "Français"),
            ("EN", "English"),
        ],
        default="FR",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("last_name", "first_name")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class StudentGuardian(models.Model):
    class Relationship(models.TextChoices):
        FATHER = "FATHER", "Père"
        MOTHER = "MOTHER", "Mère"
        GUARDIAN = "GUARDIAN", "Tuteur / tutrice"
        SIBLING = "SIBLING", "Frère / sœur"
        OTHER = "OTHER", "Autre"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="student_guardian_links",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="guardian_links",
    )
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
        related_name="student_links",
    )
    relationship = models.CharField(
        max_length=20,
        choices=Relationship.choices,
        default=Relationship.GUARDIAN,
    )
    is_primary = models.BooleanField(default=False)
    receives_notifications = models.BooleanField(default=True)
    can_receive_results = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("student__last_name", "student__first_name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "student", "guardian"),
                name="unique_guardian_link_per_student",
            ),
        ]

    def clean(self):
        errors = {}

        if self.student_id and self.student.school_id != self.school_id:
            errors["student"] = "L'élève n'appartient pas à cet établissement."

        if self.guardian_id and self.guardian.school_id != self.school_id:
            errors["guardian"] = "Le parent/tuteur n'appartient pas à cet établissement."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.student} ↔ {self.guardian}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Inscrit"
        COMPLETED = "COMPLETED", "Année terminée"
        TRANSFERRED = "TRANSFERRED", "Transféré"
        WITHDRAWN = "WITHDRAWN", "Retiré"

    class PromotionDecision(models.TextChoices):
        PENDING = "PENDING", "En attente"
        PROMOTED = "PROMOTED", "Admis / promu"
        REPEATED = "REPEATED", "Redouble"
        GRADUATED = "GRADUATED", "Diplômé"
        TRANSFERRED = "TRANSFERRED", "Transféré"
        WITHDRAWN = "WITHDRAWN", "Retiré"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    enrollment_date = models.DateField(null=True, blank=True)
    roll_number = models.CharField(max_length=40, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    final_average = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        null=True,
        blank=True,
    )
    promotion_decision = models.CharField(
        max_length=20,
        choices=PromotionDecision.choices,
        default=PromotionDecision.PENDING,
    )
    decision_reason = models.TextField(blank=True)
    next_enrollment = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        related_name="previous_enrollment",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "-academic_year__start_date",
            "classroom__name",
            "student__last_name",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("school", "student", "academic_year"),
                name="unique_student_enrollment_per_year",
            ),
        ]

    def clean(self):
        errors = {}

        if self.student_id and self.student.school_id != self.school_id:
            errors["student"] = "L'élève n'appartient pas à cet établissement."

        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            errors["academic_year"] = "L'année scolaire n'appartient pas à cet établissement."

        if self.classroom_id:
            if self.classroom.school_id != self.school_id:
                errors["classroom"] = "La classe n'appartient pas à cet établissement."

            if (
                self.academic_year_id
                and self.classroom.academic_year_id != self.academic_year_id
            ):
                errors["classroom"] = (
                    "La classe doit appartenir à l'année scolaire sélectionnée."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.student} — {self.classroom} — {self.academic_year}"
