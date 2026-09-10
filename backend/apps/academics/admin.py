from django.contrib import admin
from .models import AcademicPeriod, AcademicPolicy, AcademicYear, Classroom, Cycle, Level, LevelSubject, Section, Subject


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "period_system", "is_active", "is_closed", "start_date", "end_date")
    list_filter = ("period_system", "is_active", "is_closed")
    search_fields = ("name", "school__name", "school__slug")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "language", "order", "is_active")
    list_filter = ("language", "is_active")


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "section", "kind", "order", "is_active")
    list_filter = ("kind", "is_active")


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "cycle", "order", "is_active")


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "academic_year", "level", "capacity", "is_active")
    list_filter = ("academic_year", "is_active")


@admin.register(AcademicPolicy)
class AcademicPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "default_max_score",
        "default_promotion_threshold",
        "updated_at",
    )


@admin.register(AcademicPeriod)
class AcademicPeriodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "school",
        "academic_year",
        "kind",
        "order",
        "weight",
        "is_active",
    )
    list_filter = ("kind", "is_active", "academic_year")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "school",
        "code",
        "category",
        "default_teaching_language",
        "is_active",
    )
    search_fields = ("name", "code", "school__name")


@admin.register(LevelSubject)
class LevelSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "level",
        "school",
        "coefficient",
        "max_score_override",
        "teaching_language",
        "is_active",
    )
