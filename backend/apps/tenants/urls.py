from django.urls import path
from .views import (
    create_school,
    public_context,
    school_member_detail,
    school_members,
    school_settings,
    tenant_dashboard,
)

urlpatterns = [
    path("public/context/", public_context, name="public-context"),
    path("public/onboarding/schools/", create_school, name="create-school"),
    path("tenant/dashboard/", tenant_dashboard, name="tenant-dashboard"),
    path("tenant/settings/", school_settings, name="school-settings"),
    path("tenant/members/", school_members, name="school-members"),
    path(
        "tenant/members/<int:membership_id>/",
        school_member_detail,
        name="school-member-detail",
    ),
]
