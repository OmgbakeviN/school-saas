from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class TeachingAssignment(models.Model):
    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Affectation manuelle"
        CLASS_TEACHER_AUTO = (
            "CLASS_TEACHER_AUTO",
            "Générée depuis le titulaire de classe",
        )

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="teaching_assignments",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )
    teacher = models.ForeignKey(
        "people.Teacher",
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
    )
    source = models.CharField(
        max_length=30,
        choices=Source.choices,
        default=Source.MANUAL,
        db_index=True,
    )
    can_enter_scores = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "-academic_year__start_date",
            "classroom__level__order",
            "classroom__name",
            "subject__name",
            "teacher__last_name",
        )
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "school",
                    "academic_year",
                    "teacher",
                    "subject",
                    "classroom",
                ),
                name="unique_teaching_assignment",
            ),
        ]

    def clean(self):
        errors = {}

        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            errors["academic_year"] = "L'année scolaire n'appartient pas à cet établissement."

        if self.teacher_id and self.teacher.school_id != self.school_id:
            errors["teacher"] = "L'enseignant n'appartient pas à cet établissement."

        if self.subject_id and self.subject.school_id != self.school_id:
            errors["subject"] = "La matière n'appartient pas à cet établissement."

        if self.classroom_id:
            if self.classroom.school_id != self.school_id:
                errors["classroom"] = "La classe n'appartient pas à cet établissement."
            elif (
                self.academic_year_id
                and self.classroom.academic_year_id != self.academic_year_id
            ):
                errors["classroom"] = "La classe doit appartenir à l'année scolaire sélectionnée."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.teacher} — {self.subject} — "
            f"{self.classroom} — {self.academic_year}"
        )


class ClassroomLeadership(models.Model):
    class Role(models.TextChoices):
        CLASS_TEACHER = "CLASS_TEACHER", "Titulaire de classe"
        HOMEROOM_TEACHER = "HOMEROOM_TEACHER", "Professeur principal"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="classroom_leaderships",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="classroom_leaderships",
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        on_delete=models.PROTECT,
        related_name="leaderships",
    )
    teacher = models.ForeignKey(
        "people.Teacher",
        on_delete=models.PROTECT,
        related_name="classroom_leaderships",
    )
    role = models.CharField(max_length=30, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "-academic_year__start_date",
            "classroom__level__order",
            "classroom__name",
            "role",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("school", "academic_year", "classroom", "role"),
                condition=Q(is_active=True),
                name="unique_active_classroom_leadership_role",
            ),
        ]

    def clean(self):
        errors = {}

        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            errors["academic_year"] = "L'année scolaire n'appartient pas à cet établissement."

        if self.teacher_id and self.teacher.school_id != self.school_id:
            errors["teacher"] = "L'enseignant n'appartient pas à cet établissement."

        if self.classroom_id:
            if self.classroom.school_id != self.school_id:
                errors["classroom"] = "La classe n'appartient pas à cet établissement."
            elif (
                self.academic_year_id
                and self.classroom.academic_year_id != self.academic_year_id
            ):
                errors["classroom"] = "La classe doit appartenir à l'année scolaire sélectionnée."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_role_display()} — {self.classroom} — {self.teacher}"
