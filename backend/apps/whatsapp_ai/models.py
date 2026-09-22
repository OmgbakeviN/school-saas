from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class WhatsAppConnection(models.Model):
    class Provider(models.TextChoices):
        EVOLUTION = "EVOLUTION", "Evolution API"

    school = models.OneToOneField(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="whatsapp_connection",
    )
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.EVOLUTION,
    )
    instance_name = models.CharField(max_length=120, unique=True)
    phone_number = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("school__name",)

    def __str__(self):
        return f"{self.school.name} — {self.instance_name}"


class GuardianWhatsAppIdentity(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="guardian_whatsapp_identities",
    )
    guardian = models.OneToOneField(
        "people.Guardian",
        on_delete=models.CASCADE,
        related_name="whatsapp_identity",
    )
    normalized_phone = models.CharField(max_length=32)
    phone_verified = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("guardian__last_name", "guardian__first_name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "normalized_phone"),
                condition=~Q(normalized_phone=""),
                name="unique_guardian_whatsapp_phone_per_school",
            )
        ]

    def clean(self):
        if self.guardian_id and self.guardian.school_id != self.school_id:
            raise ValidationError(
                "Le parent et l'identité WhatsApp doivent appartenir au même établissement."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.guardian} — {self.normalized_phone}"


class StudentGuardianDocumentPermission(models.Model):
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="whatsapp_document_permissions",
    )
    student_guardian = models.OneToOneField(
        "people.StudentGuardian",
        on_delete=models.CASCADE,
        related_name="whatsapp_document_permission",
    )
    can_receive_report_cards = models.BooleanField(default=True)
    can_receive_finance = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = (
            "student_guardian__student__last_name",
            "student_guardian__student__first_name",
        )

    def clean(self):
        if (
            self.student_guardian_id
            and self.student_guardian.school_id != self.school_id
        ):
            raise ValidationError(
                "La permission et le lien parent/élève doivent appartenir au même établissement."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return str(self.student_guardian)


class WhatsAppMessageLog(models.Model):
    class Direction(models.TextChoices):
        INBOUND = "INBOUND", "Entrant"
        OUTBOUND = "OUTBOUND", "Sortant"
        SYSTEM = "SYSTEM", "Système"

    class Kind(models.TextChoices):
        TEXT = "TEXT", "Texte"
        DOCUMENT = "DOCUMENT", "Document"
        TOOL = "TOOL", "Outil IA"

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="whatsapp_message_logs",
    )
    connection = models.ForeignKey(
        WhatsAppConnection,
        on_delete=models.CASCADE,
        related_name="message_logs",
    )
    guardian = models.ForeignKey(
        "people.Guardian",
        on_delete=models.SET_NULL,
        related_name="whatsapp_message_logs",
        null=True,
        blank=True,
    )
    direction = models.CharField(max_length=20, choices=Direction.choices)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    phone = models.CharField(max_length=32)
    provider_message_id = models.CharField(max_length=160, blank=True)
    text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return f"{self.direction} {self.kind} {self.phone}"
