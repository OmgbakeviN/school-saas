from rest_framework.permissions import BasePermission

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership


REPORT_CARD_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
    SchoolMembership.Role.TEACHER,
}

PUBLISH_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
}


class CanUseReportCards(BasePermission):
    message = "Vous n'avez pas accès aux bulletins."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(
            membership
            and membership.role in REPORT_CARD_ROLES
        )


class CanPublishReportCards(BasePermission):
    message = "La publication des bulletins est réservée à la direction."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(
            membership
            and membership.role in PUBLISH_ROLES
        )
