from django.contrib import admin

from .models import ReportCardSnapshot


@admin.register(ReportCardSnapshot)
class ReportCardSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "report_type",
        "academic_period",
        "version",
        "published_at",
        "published_by",
    )
    list_filter = (
        "school",
        "academic_year",
        "report_type",
        "published_at",
    )
    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "enrollment__student__matricule",
        "verification_token",
    )
    readonly_fields = (
        "school",
        "enrollment",
        "academic_year",
        "academic_period",
        "report_type",
        "version",
        "supersedes",
        "payload",
        "payload_sha256",
        "verification_token",
        "pdf_file",
        "pdf_sha256",
        "published_by",
        "published_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
