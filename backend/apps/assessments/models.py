from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AssessmentPeriodControl(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="assessment_period_controls",
    )
    academic_period = models.OneToOneField(
        "academics.AcademicPeriod",
        on_delete=models.CASCADE,
        related_name="assessment_control",
    )
    score_entry_open = models.BooleanField(default=False)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opened_assessment_periods",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "-academic_period__academic_year__start_date",
            "academic_period__order",
        )

    def clean(self):
        if (
            self.academic_period_id
            and self.academic_period.school_id != self.school_id
        ):
            raise ValidationError({
                "academic_period": "La période n'appartient pas à cet établissement."
            })

    def __str__(self):
        state = "ouverte" if self.score_entry_open else "fermée"
        return f"{self.academic_period} — saisie {state}"


class Assessment(models.Model):
    class Kind(models.TextChoices):
        QUIZ = "QUIZ", "Interrogation"
        TEST = "TEST", "Devoir / contrôle"
        HOMEWORK = "HOMEWORK", "Travail à domicile"
        EXAM = "EXAM", "Examen"
        ORAL = "ORAL", "Oral"
        PRACTICAL = "PRACTICAL", "Pratique"
        OTHER = "OTHER", "Autre"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        INPUT = "INPUT", "Saisie en cours"
        SUBMITTED = "SUBMITTED", "Soumis"
        VALIDATED = "VALIDATED", "Validé"
        PUBLISHED = "PUBLISHED", "Publié"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    teaching_assignment = models.ForeignKey(
        "teaching.TeachingAssignment",
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    academic_period = models.ForeignKey(
        "academics.AcademicPeriod",
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    title = models.CharField(max_length=140)
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.TEST,
    )
    assessment_date = models.DateField(null=True, blank=True)
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=20,
    )
    weight = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        default=1,
    )
    instructions = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_assessments",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_assessments",
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_assessments",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    reopened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reopened_assessments",
    )
    reopened_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "-academic_period__academic_year__start_date",
            "academic_period__order",
            "teaching_assignment__classroom__level__order",
            "teaching_assignment__classroom__name",
            "teaching_assignment__subject__name",
            "-assessment_date",
            "title",
        )
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "school",
                    "teaching_assignment",
                    "academic_period",
                    "title",
                ),
                name="unique_assessment_title_per_assignment_period",
            )
        ]

    def clean(self):
        errors = {}

        if (
            self.teaching_assignment_id
            and self.teaching_assignment.school_id != self.school_id
        ):
            errors["teaching_assignment"] = (
                "L'affectation pédagogique n'appartient pas à cet établissement."
            )

        if self.academic_period_id:
            if self.academic_period.school_id != self.school_id:
                errors["academic_period"] = (
                    "La période n'appartient pas à cet établissement."
                )
            elif (
                self.teaching_assignment_id
                and self.academic_period.academic_year_id
                != self.teaching_assignment.academic_year_id
            ):
                errors["academic_period"] = (
                    "La période et l'affectation doivent appartenir à la même année scolaire."
                )

        if self.max_score is not None and self.max_score <= 0:
            errors["max_score"] = "La note maximale doit être supérieure à zéro."

        if self.weight is not None and self.weight <= 0:
            errors["weight"] = "Le poids de l'évaluation doit être supérieur à zéro."

        if errors:
            raise ValidationError(errors)

    @property
    def academic_year_id(self):
        return (
            self.teaching_assignment.academic_year_id
            if self.teaching_assignment_id
            else None
        )

    @property
    def classroom_id(self):
        return (
            self.teaching_assignment.classroom_id
            if self.teaching_assignment_id
            else None
        )

    @property
    def subject_id(self):
        return (
            self.teaching_assignment.subject_id
            if self.teaching_assignment_id
            else None
        )

    def __str__(self):
        return (
            f"{self.title} — {self.teaching_assignment.subject} — "
            f"{self.teaching_assignment.classroom}"
        )


class Grade(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="grades",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="grades",
    )
    enrollment = models.ForeignKey(
        "people.Enrollment",
        on_delete=models.PROTECT,
        related_name="grades",
    )
    score = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        null=True,
        blank=True,
    )
    is_absent = models.BooleanField(default=False)
    is_exempt = models.BooleanField(default=False)
    comment = models.CharField(max_length=255, blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_grades",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "assessment",
            "enrollment__student__last_name",
            "enrollment__student__first_name",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("school", "assessment", "enrollment"),
                name="unique_grade_per_assessment_enrollment",
            )
        ]

    def clean(self):
        errors = {}

        if self.assessment_id and self.assessment.school_id != self.school_id:
            errors["assessment"] = "L'évaluation n'appartient pas à cet établissement."

        if self.enrollment_id:
            if self.enrollment.school_id != self.school_id:
                errors["enrollment"] = "L'inscription n'appartient pas à cet établissement."
            elif self.assessment_id:
                assignment = self.assessment.teaching_assignment
                if self.enrollment.academic_year_id != assignment.academic_year_id:
                    errors["enrollment"] = "L'inscription n'est pas dans la bonne année scolaire."
                elif self.enrollment.classroom_id != assignment.classroom_id:
                    errors["enrollment"] = "L'élève n'est pas inscrit dans la classe de l'évaluation."

        if self.is_absent and self.is_exempt:
            errors["is_absent"] = "Une note ne peut pas être à la fois ABS et dispensée."

        if self.is_absent or self.is_exempt:
            if self.score is not None:
                errors["score"] = "Une absence ou dispense ne doit pas contenir de note."
        elif self.score is not None and self.assessment_id:
            if self.score < 0 or self.score > self.assessment.max_score:
                errors["score"] = (
                    f"La note doit être comprise entre 0 et {self.assessment.max_score}."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.enrollment.student} — {self.assessment} — {self.score}"
