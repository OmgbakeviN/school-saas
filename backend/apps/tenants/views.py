from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import IsSchoolAdministrator, IsTenantMember
from apps.accounts.serializers import (
    SchoolMemberCreateSerializer,
    SchoolMemberSerializer,
    SchoolMemberUpdateSerializer,
)
from .serializers import (
    SchoolOnboardingSerializer,
    SchoolSerializer,
    SchoolSettingsSerializer,
)

@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["Tenants"])
@api_view(["GET"])
@permission_classes([AllowAny])
def public_context(request):
    school = getattr(request, "school", None)
    return Response({
        "school": (
            SchoolSerializer(school, context={"request": request}).data
            if school else None
        )
    })

@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["Tenants"])
@api_view(["POST"])
@permission_classes([AllowAny])
def create_school(request):
    serializer = SchoolOnboardingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    school = serializer.save()

    return Response(
        {
            "school": SchoolSerializer(school, context={"request": request}).data,
            "message": "Établissement créé avec succès.",
        },
        status=status.HTTP_201_CREATED,
    )

@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["Tenants"])
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def tenant_dashboard(request):
    school = request.school
    membership = SchoolMembership.objects.get(
        school=school,
        user=request.user,
        is_active=True,
    )

    return Response({
        "school": SchoolSerializer(school, context={"request": request}).data,
        "user": {
            "id": request.user.id,
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        },
        "membership": {
            "role": membership.role,
            "role_label": membership.get_role_display(),
        },
        "foundation": {
            "academic_years": school.academic_years.count(),
            "students": school.students.filter(status="ACTIVE").count(),
            "teachers": school.teachers.filter(status="ACTIVE").count(),
            "classes": school.classrooms.count(),
            "members": SchoolMembership.objects.filter(
                school=school,
                is_active=True,
            ).count(),
        },
    })

@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["Tenants"])
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsTenantMember])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def school_settings(request):
    school = request.school

    if request.method == "GET":
        return Response(
            SchoolSerializer(school, context={"request": request}).data
        )

    admin_permission = IsSchoolAdministrator()
    if not admin_permission.has_permission(request, None):
        return Response(
            {"detail": admin_permission.message},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = SchoolSettingsSerializer(
        school,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        SchoolSerializer(school, context={"request": request}).data
    )

@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["Tenants"])
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSchoolAdministrator])
def school_members(request):
    school = request.school

    if request.method == "GET":
        memberships = SchoolMembership.objects.filter(
            school=school
        ).select_related("user").order_by("user__first_name", "user__last_name")
        return Response(SchoolMemberSerializer(memberships, many=True).data)

    serializer = SchoolMemberCreateSerializer(
        data=request.data,
        context={"school": school},
    )
    serializer.is_valid(raise_exception=True)
    membership = serializer.save()
    return Response(
        SchoolMemberSerializer(membership).data,
        status=status.HTTP_201_CREATED,
    )

@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["Tenants"])
@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsSchoolAdministrator])
def school_member_detail(request, membership_id):
    membership = SchoolMembership.objects.filter(
        id=membership_id,
        school=request.school,
    ).select_related("user").first()

    if not membership:
        return Response(
            {"detail": "Membre introuvable."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if membership.role == SchoolMembership.Role.OWNER:
        return Response(
            {"detail": "Le propriétaire principal ne peut pas être modifié ou supprimé ici."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.method == "DELETE":
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SchoolMemberUpdateSerializer(
        membership,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(SchoolMemberSerializer(membership).data)
