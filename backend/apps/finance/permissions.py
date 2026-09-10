from rest_framework.permissions import BasePermission

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership


FINANCE_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
    SchoolMembership.Role.ACCOUNTANT,
}

FINANCE_CONFIG_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
}


class CanUseFinance(BasePermission):
    message = "Vous n'avez pas accès à la gestion de la pension."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(
            membership
            and membership.role in FINANCE_ROLES
        )


class CanConfigureFinance(BasePermission):
    message = "La configuration des plans de pension est réservée à la direction."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(
            membership
            and membership.role in FINANCE_CONFIG_ROLES
        )
