from django.urls import path

from .views import (
    ClassroomLeadershipDetailView,
    ClassroomLeadershipListCreateView,
    MyTeachingAccessView,
    TeacherAccountView,
    TeachingAssignmentDetailView,
    TeachingAssignmentListCreateView,
)


urlpatterns = [
    path(
        "assignments/",
        TeachingAssignmentListCreateView.as_view(),
        name="teaching-assignment-list",
    ),
    path(
        "assignments/<int:pk>/",
        TeachingAssignmentDetailView.as_view(),
        name="teaching-assignment-detail",
    ),
    path(
        "leaderships/",
        ClassroomLeadershipListCreateView.as_view(),
        name="classroom-leadership-list",
    ),
    path(
        "leaderships/<int:pk>/",
        ClassroomLeadershipDetailView.as_view(),
        name="classroom-leadership-detail",
    ),
    path(
        "me/",
        MyTeachingAccessView.as_view(),
        name="my-teaching-access",
    ),
    path(
        "teachers/<int:teacher_id>/account/",
        TeacherAccountView.as_view(),
        name="teacher-account",
    ),
]
