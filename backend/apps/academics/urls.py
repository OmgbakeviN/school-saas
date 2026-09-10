from django.urls import path

from .views import (
    AcademicYearDetailView,
    AcademicYearListCreateView,
    ClassroomDetailView,
    ClassroomListCreateView,
    CycleDetailView,
    CycleListCreateView,
    LevelDetailView,
    LevelListCreateView,
    LevelSubjectDetailView,
    LevelSubjectListCreateView,
    SectionDetailView,
    SectionListCreateView,
    SubjectDetailView,
    SubjectListCreateView,
    AcademicPeriodDetailView,
    AcademicPeriodListCreateView,
    academic_policy,
    bootstrap_periods,
    bootstrap_structure,
    bulk_assign_subject,
)

urlpatterns = [
    path("years/", AcademicYearListCreateView.as_view(), name="academic-year-list"),
    path("years/<int:pk>/", AcademicYearDetailView.as_view(), name="academic-year-detail"),

    path("sections/", SectionListCreateView.as_view(), name="section-list"),
    path("sections/<int:pk>/", SectionDetailView.as_view(), name="section-detail"),

    path("cycles/", CycleListCreateView.as_view(), name="cycle-list"),
    path("cycles/<int:pk>/", CycleDetailView.as_view(), name="cycle-detail"),

    path("levels/", LevelListCreateView.as_view(), name="level-list"),
    path("levels/<int:pk>/", LevelDetailView.as_view(), name="level-detail"),

    path("classrooms/", ClassroomListCreateView.as_view(), name="classroom-list"),
    path("classrooms/<int:pk>/", ClassroomDetailView.as_view(), name="classroom-detail"),

    path("bootstrap/", bootstrap_structure, name="academic-bootstrap"),

    path("policy/", academic_policy, name="academic-policy"),

    path("periods/", AcademicPeriodListCreateView.as_view(), name="academic-period-list"),
    path("periods/<int:pk>/", AcademicPeriodDetailView.as_view(), name="academic-period-detail"),
    path("periods/bootstrap/", bootstrap_periods, name="academic-period-bootstrap"),

    path("subjects/", SubjectListCreateView.as_view(), name="subject-list"),
    path("subjects/<int:pk>/", SubjectDetailView.as_view(), name="subject-detail"),

    path("level-subjects/", LevelSubjectListCreateView.as_view(), name="level-subject-list"),
    path("level-subjects/bulk/", bulk_assign_subject, name="level-subject-bulk"),
    path("level-subjects/<int:pk>/", LevelSubjectDetailView.as_view(), name="level-subject-detail"),
]
