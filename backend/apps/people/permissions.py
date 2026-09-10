from rest_framework.permissions import BasePermission

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership


class PeopleManagementPermission(BasePermission):
    message = "Vous n'avez pas accès à la gestion des personnes."

    def has_permission(self, request, view):
        membership = get_school_membership(request)

        if not membership:
            return False

        return membership.role in {
            SchoolMembership.Role.OWNER,
            SchoolMembership.Role.DIRECTOR,
            SchoolMembership.Role.MANAGER,
        }
