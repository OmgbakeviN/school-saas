from django.contrib import admin
from .models import School,SchoolDomain
class DomainInline(admin.TabularInline):
    model=SchoolDomain
    extra=0
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display=("name","slug","language_mode","education_level","teaching_model","status")
    list_filter=("language_mode","education_level","teaching_model","status")
    search_fields=("name","slug")
    inlines=[DomainInline]
@admin.register(SchoolDomain)
class DomainAdmin(admin.ModelAdmin):
    list_display=("domain","school","is_primary","is_local")
