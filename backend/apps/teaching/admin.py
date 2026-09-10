from django.contrib import admin

from .models import ClassroomLeadership, TeachingAssignment


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "subject",
        "classroom",
        "academic_year",
        "source",
        "can_enter_scores",
        "is_active",
    )
    list_filter = (
        "school",
        "academic_year",
        "source",
        "can_enter_scores",
        "is_active",
    )
    search_fields = (
        "teacher__first_name",
        "teacher__last_name",
        "subject__name",
        "classroom__name",
    )


@admin.register(ClassroomLeadership)
class ClassroomLeadershipAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "role",
        "classroom",
        "academic_year",
        "is_active",
    )
    list_filter = ("school", "academic_year", "role", "is_active")
    search_fields = (
        "teacher__first_name",
        "teacher__last_name",
        "classroom__name",
    )
