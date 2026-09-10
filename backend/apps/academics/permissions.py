from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership


class AcademicStructurePermission(BasePermission):
    message = "Vous n'avez pas l'autorisation de modifier la structure académique."

    def has_permission(self, request, view):
        membership = get_school_membership(request)

        if not membership:
            return False

        if request.method in SAFE_METHODS:
            return True

        return membership.role in {
            SchoolMembership.Role.OWNER,
            SchoolMembership.Role.DIRECTOR,
        }
