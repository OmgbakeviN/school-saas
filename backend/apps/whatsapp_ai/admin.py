from django.contrib import admin

from .models import (
    GuardianWhatsAppIdentity,
    StudentGuardianDocumentPermission,
    WhatsAppConnection,
    WhatsAppMessageLog,
)


@admin.register(WhatsAppConnection)
class WhatsAppConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "instance_name",
        "provider",
        "phone_number",
        "is_active",
        "updated_at",
    )
    list_filter = ("provider", "is_active")
    search_fields = ("school__name", "school__slug", "instance_name", "phone_number")


@admin.register(GuardianWhatsAppIdentity)
class GuardianWhatsAppIdentityAdmin(admin.ModelAdmin):
    list_display = (
        "guardian",
        "school",
        "normalized_phone",
        "phone_verified",
        "whatsapp_enabled",
        "verified_at",
    )
    list_filter = ("school", "phone_verified", "whatsapp_enabled")
    search_fields = (
        "guardian__first_name",
        "guardian__last_name",
        "normalized_phone",
    )


@admin.register(StudentGuardianDocumentPermission)
class StudentGuardianDocumentPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "student_guardian",
        "school",
        "can_receive_report_cards",
        "can_receive_finance",
    )
    list_filter = (
        "school",
        "can_receive_report_cards",
        "can_receive_finance",
    )


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "school",
        "direction",
        "kind",
        "phone",
        "provider_message_id",
    )
    list_filter = ("school", "direction", "kind")
    search_fields = ("phone", "text", "provider_message_id")
    readonly_fields = (
        "school",
        "connection",
        "guardian",
        "direction",
        "kind",
        "phone",
        "provider_message_id",
        "text",
        "metadata",
        "created_at",
    )
