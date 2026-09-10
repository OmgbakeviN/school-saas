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
