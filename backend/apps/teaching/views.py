from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import IsSchoolAdministrator, IsTenantMember, get_school_membership
from apps.people.models import Teacher

from .models import ClassroomLeadership, TeachingAssignment
from .permissions import TeachingManagementPermission
from .serializers import (
    ClassroomLeadershipSerializer,
    MyTeachingAccessSerializer,
    TeacherAccountProvisionSerializer,
    TeacherAccountResultSerializer,
    TeachingAssignmentSerializer,
)
from .services import (
    get_teacher_profile_for_user,
    sync_classroom_class_teacher_assignments,
    sync_school_class_teacher_assignments,
)


class TeachingAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = TeachingAssignmentSerializer
    permission_classes = [IsAuthenticated, TeachingManagementPermission]

    def get_queryset(self):
        sync_school_class_teacher_assignments(
            school=self.request.school,
            academic_year_id=self.request.query_params.get("academic_year") or None,
            classroom_id=self.request.query_params.get("classroom") or None,
        )
        queryset = TeachingAssignment.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_year",
            "teacher",
            "subject",
            "classroom",
            "classroom__level",
            "classroom__level__cycle",
            "classroom__level__cycle__section",
        )

        filters = {
            "academic_year_id": self.request.query_params.get("academic_year"),
            "teacher_id": self.request.query_params.get("teacher"),
            "subject_id": self.request.query_params.get("subject"),
            "classroom_id": self.request.query_params.get("classroom"),
        }
        for field, value in filters.items():
            if value:
                queryset = queryset.filter(**{field: value})

        active = self.request.query_params.get("active")
        if active in {"true", "false"}:
            queryset = queryset.filter(is_active=active == "true")

        return queryset


class TeachingAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeachingAssignmentSerializer
    permission_classes = [IsAuthenticated, TeachingManagementPermission]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.source == TeachingAssignment.Source.CLASS_TEACHER_AUTO:
            return Response(
                {
                    "detail": (
                        "Cette affectation est gérée automatiquement depuis le "
                        "titulaire de classe. Modifiez le titulaire ou le programme."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        return TeachingAssignment.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_year",
            "teacher",
            "subject",
            "classroom",
            "classroom__level",
            "classroom__level__cycle",
            "classroom__level__cycle__section",
        )


class ClassroomLeadershipListCreateView(generics.ListCreateAPIView):
    serializer_class = ClassroomLeadershipSerializer
    permission_classes = [IsAuthenticated, TeachingManagementPermission]

    def get_queryset(self):
        queryset = ClassroomLeadership.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_year",
            "teacher",
            "classroom",
            "classroom__level",
        )

        academic_year = self.request.query_params.get("academic_year")
        classroom = self.request.query_params.get("classroom")
        role = self.request.query_params.get("role")

        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        if classroom:
            queryset = queryset.filter(classroom_id=classroom)
        if role:
            queryset = queryset.filter(role=role)

        return queryset


class ClassroomLeadershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClassroomLeadershipSerializer
    permission_classes = [IsAuthenticated, TeachingManagementPermission]

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        school = instance.school
        year_id = instance.academic_year_id
        classroom_id = instance.classroom_id
        response = super().destroy(request, *args, **kwargs)
        sync_classroom_class_teacher_assignments(
            school=school,
            academic_year_id=year_id,
            classroom_id=classroom_id,
        )
        return response

    def get_queryset(self):
        return ClassroomLeadership.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_year",
            "teacher",
            "classroom",
            "classroom__level",
        )


class MyTeachingAccessView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="Mes affectations pédagogiques",
        responses={200: MyTeachingAccessSerializer},
        tags=["Teaching"],
    )
    def get(self, request):
        membership = get_school_membership(request)
        teacher = get_teacher_profile_for_user(
            user=request.user,
            school=request.school,
        )

        if membership.role == SchoolMembership.Role.TEACHER and not teacher:
            return Response(
                {
                    "detail": (
                        "Votre compte enseignant n'est pas encore lié à un profil enseignant. "
                        "La direction doit effectuer cette liaison."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if not teacher:
            return Response({
                "teacher": None,
                "assignments": [],
                "leaderships": [],
            })

        sync_school_class_teacher_assignments(
            school=request.school,
        )

        assignments = TeachingAssignment.objects.filter(
            school=request.school,
            teacher=teacher,
            is_active=True,
        ).select_related(
            "academic_year",
            "subject",
            "classroom",
            "classroom__level",
            "classroom__level__cycle",
            "classroom__level__cycle__section",
            "teacher",
        )

        leaderships = ClassroomLeadership.objects.filter(
            school=request.school,
            teacher=teacher,
            is_active=True,
        ).select_related(
            "academic_year",
            "classroom",
            "classroom__level",
            "teacher",
        )

        payload = {
            "teacher": {
                "id": teacher.id,
                "employee_number": teacher.employee_number,
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "email": teacher.email,
            },
            "assignments": TeachingAssignmentSerializer(
                assignments,
                many=True,
                context={"request": request},
            ).data,
            "leaderships": ClassroomLeadershipSerializer(
                leaderships,
                many=True,
                context={"request": request},
            ).data,
        }
        return Response(payload)


class TeacherAccountView(APIView):
    permission_classes = [IsAuthenticated, IsSchoolAdministrator]

    def get_teacher(self, request, teacher_id):
        return Teacher.objects.filter(
            school=request.school,
            id=teacher_id,
        ).select_related("user").first()

    @extend_schema(
        summary="Créer ou lier le compte de connexion d'un enseignant",
        request=TeacherAccountProvisionSerializer,
        responses={201: TeacherAccountResultSerializer},
        tags=["Teaching"],
    )
    def post(self, request, teacher_id):
        teacher = self.get_teacher(request, teacher_id)
        if not teacher:
            return Response(
                {"detail": "Enseignant introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TeacherAccountProvisionSerializer(
            data=request.data,
            context={"request": request, "teacher": teacher},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        response = {
            "teacher_id": teacher.id,
            "user_id": result["user"].id,
            "email": result["user"].email,
            "role": result["membership"].role,
            "created_user": result["created_user"],
            "created_membership": result["created_membership"],
        }
        return Response(response, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Révoquer l'accès de connexion d'un enseignant",
        responses={204: None},
        tags=["Teaching"],
    )
    @transaction.atomic
    def delete(self, request, teacher_id):
        teacher = self.get_teacher(request, teacher_id)
        if not teacher:
            return Response(
                {"detail": "Enseignant introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = teacher.user
        if user:
            SchoolMembership.objects.filter(
                school=request.school,
                user=user,
                role=SchoolMembership.Role.TEACHER,
            ).update(is_active=False)

        teacher.user = None
        teacher.save(update_fields=["user", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
