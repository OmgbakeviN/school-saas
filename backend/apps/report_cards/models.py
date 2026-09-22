import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def generate_verification_token():
    return secrets.token_urlsafe(32)


def report_card_pdf_upload_to(instance, filename):
    period = (
        f"period-{instance.academic_period_id}"
        if instance.academic_period_id
        else "annual"
    )
    return (
        f"report_cards/{instance.school_id}/"
        f"{instance.academic_year_id}/{period}/"
        f"student-{instance.enrollment.student_id}/"
        f"v{instance.version}/{filename}"
    )


class ReportCardTemplate(models.Model):
    class LanguageMode(models.TextChoices):
        AUTO = "AUTO", "Automatique"
        FRENCH = "FRENCH", "Français"
        ENGLISH = "ENGLISH", "English"

    class TemplateKey(models.TextChoices):
        CLASSIC = "CLASSIC", "Classique"
        MODERN = "MODERN", "Moderne"
        COMPACT = "COMPACT", "Compact"
        SECONDARY_LANDSCAPE = (
            "SECONDARY_LANDSCAPE",
            "Secondaire paysage",
        )

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="report_card_templates",
    )
    cycle = models.ForeignKey(
        "academics.Cycle",
        on_delete=models.PROTECT,
        related_name="report_card_templates",
        null=True,
        blank=True,
        help_text=(
            "Vide = modèle valable pour tous les cycles de l'établissement."
        ),
    )
    name = models.CharField(max_length=120)
    template_key = models.CharField(
        max_length=40,
        choices=TemplateKey.choices,
        default=TemplateKey.CLASSIC,
    )
    version = models.PositiveIntegerField(default=1)
    is_default = models.BooleanField(default=False)
    language_mode = models.CharField(
        max_length=20,
        choices=LanguageMode.choices,
        default=LanguageMode.AUTO,
    )

    show_rank = models.BooleanField(default=True)
    show_class_average = models.BooleanField(default=True)
    show_effective = models.BooleanField(default=True)
    show_decision = models.BooleanField(default=True)
    show_subject_comments = models.BooleanField(default=True)
    show_teacher_comment = models.BooleanField(default=True)
    show_direction_comment = models.BooleanField(default=True)
    show_student_photo = models.BooleanField(default=False)
    show_qr = models.BooleanField(default=True)

    font_scale = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default="1.00",
        help_text="Échelle entre 0.80 et 1.10.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "cycle__order",
            "-is_default",
            "name",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("school", "cycle", "name"),
                name="unique_report_card_template_name_per_scope",
            ),
        ]

    @property
    def orientation(self):
        return (
            "LANDSCAPE"
            if self.template_key == self.TemplateKey.SECONDARY_LANDSCAPE
            else "PORTRAIT"
        )

    def clean(self):
        errors = {}

        if self.cycle_id and self.cycle.school_id != self.school_id:
            errors["cycle"] = (
                "Le cycle n'appartient pas à cet établissement."
            )

        scale = float(self.font_scale or 1)
        if scale < 0.80 or scale > 1.10:
            errors["font_scale"] = (
                "L'échelle doit être comprise entre 0.80 et 1.10."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.is_default:
            queryset = ReportCardTemplate.objects.filter(
                school=self.school,
            )
            if self.cycle_id:
                queryset = queryset.filter(cycle=self.cycle)
            else:
                queryset = queryset.filter(cycle__isnull=True)

            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            queryset.update(is_default=False)

        return super().save(*args, **kwargs)

    def __str__(self):
        scope = self.cycle.name if self.cycle_id else "Tous les cycles"
        return f"{self.name} - {scope}"


class ReportCardSnapshot(models.Model):
    class ReportType(models.TextChoices):
        PERIOD = "PERIOD", "Bulletin de période"
        ANNUAL = "ANNUAL", "Bulletin annuel"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.PROTECT,
        related_name="report_card_snapshots",
    )
    enrollment = models.ForeignKey(
        "people.Enrollment",
        on_delete=models.PROTECT,
        related_name="report_card_snapshots",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="report_card_snapshots",
    )
    academic_period = models.ForeignKey(
        "academics.AcademicPeriod",
        on_delete=models.PROTECT,
        related_name="report_card_snapshots",
        null=True,
        blank=True,
    )
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
    )
    version = models.PositiveIntegerField()
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="newer_versions",
        null=True,
        blank=True,
    )

    payload = models.JSONField()
    payload_sha256 = models.CharField(max_length=64)
    verification_token = models.CharField(
        max_length=80,
        unique=True,
        default=generate_verification_token,
        editable=False,
    )

    pdf_file = models.FileField(
        upload_to=report_card_pdf_upload_to,
        max_length=500,
    )
    pdf_sha256 = models.CharField(max_length=64)

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_report_cards",
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-published_at", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "school",
                    "enrollment",
                    "report_type",
                    "academic_period",
                    "version",
                ),
                name="unique_period_report_card_version",
                condition=models.Q(report_type="PERIOD"),
            ),
            models.UniqueConstraint(
                fields=(
                    "school",
                    "enrollment",
                    "report_type",
                    "academic_year",
                    "version",
                ),
                name="unique_annual_report_card_version",
                condition=models.Q(report_type="ANNUAL"),
            ),
        ]

    def clean(self):
        errors = {}

        if self.enrollment_id:
            if self.enrollment.school_id != self.school_id:
                errors["enrollment"] = "L'inscription n'appartient pas à cet établissement."
            if self.enrollment.academic_year_id != self.academic_year_id:
                errors["academic_year"] = (
                    "Le bulletin doit appartenir à l'année de l'inscription."
                )

        if self.report_type == self.ReportType.PERIOD:
            if not self.academic_period_id:
                errors["academic_period"] = (
                    "Une période est obligatoire pour un bulletin de période."
                )
            elif self.academic_period.academic_year_id != self.academic_year_id:
                errors["academic_period"] = (
                    "La période n'appartient pas à l'année scolaire du bulletin."
                )

        if self.report_type == self.ReportType.ANNUAL and self.academic_period_id:
            errors["academic_period"] = (
                "Un bulletin annuel ne doit pas être lié à une période."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Un snapshot officiel ne doit jamais être modifié après sa création.
        if self.pk:
            raise ValidationError(
                "Un bulletin publié est immuable. Créez une nouvelle version."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        scope = (
            self.academic_period.name
            if self.academic_period_id
            else "Annuel"
        )
        return (
            f"{self.enrollment.student} - {scope} - "
            f"v{self.version}"
        )
