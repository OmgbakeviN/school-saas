from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0001_initial"),
        ("tenants", "0002_school_branding"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppConnection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[("EVOLUTION", "Evolution API")],
                        default="EVOLUTION",
                        max_length=20,
                    ),
                ),
                ("instance_name", models.CharField(max_length=120, unique=True)),
                ("phone_number", models.CharField(blank=True, max_length=40)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "school",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whatsapp_connection",
                        to="tenants.school",
                    ),
                ),
            ],
            options={"ordering": ("school__name",)},
        ),
        migrations.CreateModel(
            name="GuardianWhatsAppIdentity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("normalized_phone", models.CharField(max_length=32)),
                ("phone_verified", models.BooleanField(default=False)),
                ("whatsapp_enabled", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "guardian",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whatsapp_identity",
                        to="people.guardian",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="guardian_whatsapp_identities",
                        to="tenants.school",
                    ),
                ),
            ],
            options={
                "ordering": ("guardian__last_name", "guardian__first_name"),
            },
        ),
        migrations.AddConstraint(
            model_name="guardianwhatsappidentity",
            constraint=models.UniqueConstraint(
                condition=~Q(normalized_phone=""),
                fields=("school", "normalized_phone"),
                name="unique_guardian_whatsapp_phone_per_school",
            ),
        ),
        migrations.CreateModel(
            name="StudentGuardianDocumentPermission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("can_receive_report_cards", models.BooleanField(default=True)),
                ("can_receive_finance", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whatsapp_document_permissions",
                        to="tenants.school",
                    ),
                ),
                (
                    "student_guardian",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whatsapp_document_permission",
                        to="people.studentguardian",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "student_guardian__student__last_name",
                    "student_guardian__student__first_name",
                )
            },
        ),
        migrations.CreateModel(
            name="WhatsAppMessageLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[
                            ("INBOUND", "Entrant"),
                            ("OUTBOUND", "Sortant"),
                            ("SYSTEM", "Système"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("TEXT", "Texte"),
                            ("DOCUMENT", "Document"),
                            ("TOOL", "Outil IA"),
                        ],
                        max_length=20,
                    ),
                ),
                ("phone", models.CharField(max_length=32)),
                ("provider_message_id", models.CharField(blank=True, max_length=160)),
                ("text", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "connection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="message_logs",
                        to="whatsapp_ai.whatsappconnection",
                    ),
                ),
                (
                    "guardian",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="whatsapp_message_logs",
                        to="people.guardian",
                    ),
                ),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whatsapp_message_logs",
                        to="tenants.school",
                    ),
                ),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
    ]
