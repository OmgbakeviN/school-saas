from rest_framework.permissions import BasePermission

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership


TEACHING_MANAGEMENT_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
}


class TeachingManagementPermission(BasePermission):
    message = "Cette action est réservée à la direction ou à la gestion pédagogique."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(membership and membership.role in TEACHING_MANAGEMENT_ROLES)
