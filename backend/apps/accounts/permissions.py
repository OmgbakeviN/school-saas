from rest_framework.permissions import BasePermission
from .models import SchoolMembership

ADMIN_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
}

def get_school_membership(request):
    school = getattr(request, "school", None)
    user = getattr(request, "user", None)

    if not school or not user or not user.is_authenticated:
        return None

    return SchoolMembership.objects.filter(
        school=school,
        user=user,
        is_active=True,
    ).first()

class IsTenantMember(BasePermission):
    message = "Vous n'appartenez pas à cet établissement."

    def has_permission(self, request, view):
        return get_school_membership(request) is not None

class IsSchoolAdministrator(BasePermission):
    message = "Cette action est réservée à la direction de l'établissement."

    def has_permission(self, request, view):
        membership = get_school_membership(request)
        return bool(membership and membership.role in ADMIN_ROLES)
