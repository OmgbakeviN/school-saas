from django.contrib import admin

from .models import Enrollment, Guardian, Student, StudentGuardian, Teacher


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "matricule",
        "last_name",
        "first_name",
        "school",
        "status",
    )
    list_filter = ("status", "school")
    search_fields = (
        "matricule",
        "first_name",
        "last_name",
        "school__name",
    )


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "last_name",
        "first_name",
        "school",
        "speciality",
        "status",
    )
    list_filter = ("status", "school")
    search_fields = (
        "employee_number",
        "first_name",
        "last_name",
        "email",
    )


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "phone",
        "school",
        "preferred_language",
        "is_active",
    )
    list_filter = ("preferred_language", "is_active", "school")
    search_fields = (
        "first_name",
        "last_name",
        "phone",
        "email",
    )


@admin.register(StudentGuardian)
class StudentGuardianAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "guardian",
        "relationship",
        "is_primary",
        "receives_notifications",
        "can_receive_results",
    )
    list_filter = (
        "relationship",
        "is_primary",
        "receives_notifications",
        "can_receive_results",
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "academic_year",
        "classroom",
        "status",
        "promotion_decision",
        "school",
    )
    list_filter = (
        "academic_year",
        "status",
        "promotion_decision",
        "school",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__matricule",
        "classroom__name",
    )
