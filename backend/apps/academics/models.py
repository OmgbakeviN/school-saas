from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AcademicYear(models.Model):
    class PeriodSystem(models.TextChoices):
        TRIMESTER = "TRIMESTER", "Trimestres"
        SEMESTER = "SEMESTER", "Semestres"
        CUSTOM = "CUSTOM", "Personnalisé"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="academic_years",
    )
    name = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    period_system = models.CharField(
        max_length=20,
        choices=PeriodSystem.choices,
        default=PeriodSystem.TRIMESTER,
    )
    is_active = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_date",)
        constraints = [
            models.UniqueConstraint(
                fields=("school", "name"),
                name="unique_academic_year_name_per_school",
            ),
            models.UniqueConstraint(
                fields=("school",),
                condition=Q(is_active=True),
                name="unique_active_academic_year_per_school",
            ),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({
                "end_date": "La date de fin doit être postérieure à la date de début."
            })

    def __str__(self):
        return f"{self.school.slug} - {self.name}"


class Section(models.Model):
    class Language(models.TextChoices):
        FRENCH = "FRENCH", "Francophone"
        ENGLISH = "ENGLISH", "Anglophone"
        BILINGUAL = "BILINGUAL", "Bilingue"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="academic_sections",
    )
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=30)
    language = models.CharField(
        max_length=20,
        choices=Language.choices,
        default=Language.FRENCH,
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "code"),
                name="unique_section_code_per_school",
            ),
        ]

    def __str__(self):
        return f"{self.school.slug} - {self.name}"


class Cycle(models.Model):
    class Kind(models.TextChoices):
        PRIMARY = "PRIMARY", "Primaire"
        SECONDARY = "SECONDARY", "Secondaire"
        OTHER = "OTHER", "Autre"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="academic_cycles",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="cycles",
    )
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=40)
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.SECONDARY,
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    max_score_override = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    promotion_threshold_override = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("section__order", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "code"),
                name="unique_cycle_code_per_school",
            ),
        ]

    def clean(self):
        if self.section_id and self.section.school_id != self.school_id:
            raise ValidationError("La section et le cycle doivent appartenir au même établissement.")

    def __str__(self):
        return f"{self.section.name} / {self.name}"


class Level(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="academic_levels",
    )
    cycle = models.ForeignKey(
        Cycle,
        on_delete=models.PROTECT,
        related_name="levels",
    )
    name = models.CharField(max_length=80)
    code = models.SlugField(max_length=40)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    max_score_override = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    promotion_threshold_override = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("cycle__order", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "cycle", "code"),
                name="unique_level_code_per_cycle",
            ),
        ]

    def clean(self):
        if self.cycle_id and self.cycle.school_id != self.school_id:
            raise ValidationError("Le niveau et le cycle doivent appartenir au même établissement.")

    def __str__(self):
        return f"{self.cycle.name} / {self.name}"


class Classroom(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="classrooms",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="classrooms",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name="classrooms",
    )
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50)
    capacity = models.PositiveSmallIntegerField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("level__order", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "academic_year", "code"),
                name="unique_classroom_code_per_year",
            ),
        ]

    def clean(self):
        errors = {}

        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            errors["academic_year"] = "L'année scolaire n'appartient pas à cet établissement."

        if self.level_id and self.level.school_id != self.school_id:
            errors["level"] = "Le niveau n'appartient pas à cet établissement."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


class AcademicPolicy(models.Model):
    school = models.OneToOneField(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="academic_policy",
    )
    default_max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=20,
    )
    default_promotion_threshold = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=10,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.default_max_score <= 0:
            raise ValidationError({
                "default_max_score": "La note maximale doit être supérieure à zéro."
            })

        if (
            self.default_promotion_threshold < 0
            or self.default_promotion_threshold > self.default_max_score
        ):
            raise ValidationError({
                "default_promotion_threshold": (
                    "Le seuil de passage doit être compris entre 0 et la note maximale."
                )
            })

    def __str__(self):
        return f"Academic policy - {self.school.slug}"


class AcademicPeriod(models.Model):
    class Kind(models.TextChoices):
        TRIMESTER = "TRIMESTER", "Trimestre"
        SEMESTER = "SEMESTER", "Semestre"
        CUSTOM = "CUSTOM", "Personnalisé"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="academic_periods",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="periods",
    )
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=40)
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.TRIMESTER,
    )
    order = models.PositiveSmallIntegerField(default=1)
    weight = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        default=1,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("academic_year__start_date", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "academic_year", "code"),
                name="unique_period_code_per_year",
            ),
        ]

    def clean(self):
        errors = {}

        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            errors["academic_year"] = "L'année scolaire n'appartient pas à cet établissement."

        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors["end_date"] = "La date de fin doit être postérieure à la date de début."

        if self.weight <= 0:
            errors["weight"] = "Le poids doit être supérieur à zéro."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"


class Subject(models.Model):
    class Language(models.TextChoices):
        DEFAULT = "DEFAULT", "Langue de la section"
        FRENCH = "FRENCH", "Français"
        ENGLISH = "ENGLISH", "Anglais"
        BILINGUAL = "BILINGUAL", "Bilingue"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=50)
    category = models.CharField(max_length=80, blank=True)
    default_teaching_language = models.CharField(
        max_length=20,
        choices=Language.choices,
        default=Language.DEFAULT,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("school", "code"),
                name="unique_subject_code_per_school",
            ),
        ]

    def __str__(self):
        return self.name


class LevelSubject(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="level_subjects",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="subject_configs",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="level_configs",
    )
    coefficient = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        default=1,
    )
    max_score_override = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teaching_language = models.CharField(
        max_length=20,
        choices=Subject.Language.choices,
        default=Subject.Language.DEFAULT,
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("level__order", "order", "subject__name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "level", "subject"),
                name="unique_subject_per_level",
            ),
        ]

    def clean(self):
        errors = {}

        if self.level_id and self.level.school_id != self.school_id:
            errors["level"] = "Le niveau n'appartient pas à cet établissement."

        if self.subject_id and self.subject.school_id != self.school_id:
            errors["subject"] = "La matière n'appartient pas à cet établissement."

        if self.coefficient <= 0:
            errors["coefficient"] = "Le coefficient doit être supérieur à zéro."

        if self.max_score_override is not None and self.max_score_override <= 0:
            errors["max_score_override"] = "La note maximale doit être supérieure à zéro."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.level.name} - {self.subject.name}"
