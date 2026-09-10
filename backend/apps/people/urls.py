from django.urls import path

from .operations_views import (
    ApplyPromotionsView,
    BulkClassAssignmentView,
    EnrollmentExportView,
    ExitStudentsView,
    GuardianExportView,
    GuardianImportTemplateView,
    GuardianImportView,
    PrepareAcademicYearView,
    PromotionPreviewView,
    ReEnrollRepeatersView,
    StudentExportView,
    StudentImportTemplateView,
    StudentImportView,
    TeacherExportView,
    TeacherImportTemplateView,
    TeacherImportView,
)
from .views import (
    EnrollmentDetailView,
    EnrollmentListCreateView,
    GuardianDetailView,
    GuardianListCreateView,
    StudentDetailView,
    StudentGuardianDetailView,
    StudentGuardianListCreateView,
    StudentListCreateView,
    TeacherDetailView,
    TeacherListCreateView,
    people_summary,
)


urlpatterns = [
    # Dashboard / CRUD
    path(
        "summary/",
        people_summary,
        name="people-summary",
    ),
    path(
        "students/",
        StudentListCreateView.as_view(),
        name="student-list",
    ),
    path(
        "students/<int:pk>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),
    path(
        "teachers/",
        TeacherListCreateView.as_view(),
        name="teacher-list",
    ),
    path(
        "teachers/<int:pk>/",
        TeacherDetailView.as_view(),
        name="teacher-detail",
    ),
    path(
        "guardians/",
        GuardianListCreateView.as_view(),
        name="guardian-list",
    ),
    path(
        "guardians/<int:pk>/",
        GuardianDetailView.as_view(),
        name="guardian-detail",
    ),
    path(
        "guardian-links/",
        StudentGuardianListCreateView.as_view(),
        name="guardian-link-list",
    ),
    path(
        "guardian-links/<int:pk>/",
        StudentGuardianDetailView.as_view(),
        name="guardian-link-detail",
    ),
    path(
        "enrollments/",
        EnrollmentListCreateView.as_view(),
        name="enrollment-list",
    ),
    path(
        "enrollments/<int:pk>/",
        EnrollmentDetailView.as_view(),
        name="enrollment-detail",
    ),

    # Imports
    path(
        "imports/students/",
        StudentImportView.as_view(),
        name="student-import",
    ),
    path(
        "imports/teachers/",
        TeacherImportView.as_view(),
        name="teacher-import",
    ),
    path(
        "imports/guardians/",
        GuardianImportView.as_view(),
        name="guardian-import",
    ),
    path(
        "imports/templates/students/",
        StudentImportTemplateView.as_view(),
        name="student-import-template",
    ),
    path(
        "imports/templates/teachers/",
        TeacherImportTemplateView.as_view(),
        name="teacher-import-template",
    ),
    path(
        "imports/templates/guardians/",
        GuardianImportTemplateView.as_view(),
        name="guardian-import-template",
    ),

    # Bulk enrollment
    path(
        "bulk/class-assignment/",
        BulkClassAssignmentView.as_view(),
        name="bulk-class-assignment",
    ),

    # Year-end
    path(
        "promotions/preview/",
        PromotionPreviewView.as_view(),
        name="promotion-preview",
    ),
    path(
        "promotions/apply/",
        ApplyPromotionsView.as_view(),
        name="promotion-apply",
    ),
    path(
        "promotions/re-enroll-repeaters/",
        ReEnrollRepeatersView.as_view(),
        name="re-enroll-repeaters",
    ),
    path(
        "promotions/exit/",
        ExitStudentsView.as_view(),
        name="promotion-exit",
    ),

    # New academic year
    path(
        "academic-years/prepare/",
        PrepareAcademicYearView.as_view(),
        name="prepare-academic-year",
    ),

    # Exports
    path(
        "exports/students/",
        StudentExportView.as_view(),
        name="student-export",
    ),
    path(
        "exports/teachers/",
        TeacherExportView.as_view(),
        name="teacher-export",
    ),
    path(
        "exports/guardians/",
        GuardianExportView.as_view(),
        name="guardian-export",
    ),
    path(
        "exports/enrollments/",
        EnrollmentExportView.as_view(),
        name="enrollment-export",
    ),
]
