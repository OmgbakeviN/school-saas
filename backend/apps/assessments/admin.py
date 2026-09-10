from django.contrib import admin

from .models import Assessment, AssessmentPeriodControl, Grade


@admin.register(AssessmentPeriodControl)
class AssessmentPeriodControlAdmin(admin.ModelAdmin):
    list_display = (
        "academic_period",
        "school",
        "score_entry_open",
        "updated_at",
    )
    list_filter = ("score_entry_open", "school")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teaching_assignment",
        "academic_period",
        "status",
        "max_score",
        "weight",
    )
    list_filter = ("status", "kind", "school")
    search_fields = (
        "title",
        "teaching_assignment__teacher__last_name",
        "teaching_assignment__subject__name",
        "teaching_assignment__classroom__name",
    )


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "assessment",
        "enrollment",
        "score",
        "is_absent",
        "is_exempt",
        "updated_at",
    )
    list_filter = ("is_absent", "is_exempt", "school")
