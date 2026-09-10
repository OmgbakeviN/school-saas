from rest_framework.permissions import BasePermission

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership


ASSESSMENT_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
    SchoolMembership.Role.TEACHER,
}

ASSESSMENT_MANAGEMENT_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
}

DIRECTION_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
}


class CanUseAssessments(BasePermission):
    message = "Vous n'avez pas accès aux évaluations de cet établissement."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(membership and membership.role in ASSESSMENT_ROLES)


class CanManageAssessments(BasePermission):
    message = "Cette action est réservée à l'administration pédagogique."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(membership and membership.role in ASSESSMENT_MANAGEMENT_ROLES)


class IsAssessmentDirection(BasePermission):
    message = "Cette action doit être validée par la direction."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(membership and membership.role in DIRECTION_ROLES)
