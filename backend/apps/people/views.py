from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.db.models import Count, Prefetch, Q
from django.db.models.deletion import ProtectedError
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .image_utils import StudentPhotoError, compress_student_photo
from .models import Enrollment, Guardian, Student, StudentGuardian, Teacher
from .permissions import PeopleManagementPermission
from .serializers import (
    EnrollmentSerializer,
    GuardianSerializer,
    PeopleSummarySerializer,
    StudentGuardianSerializer,
    StudentSerializer,
    TeacherSerializer,
)


class TenantScopedListCreateView(generics.ListCreateAPIView):
    permission_classes = [PeopleManagementPermission]

    def get_queryset(self):
        return self.queryset.filter(school=self.request.school)


class TenantScopedDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [PeopleManagementPermission]

    def get_queryset(self):
        return self.queryset.filter(school=self.request.school)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Cet élément est déjà utilisé dans l'historique. "
                        "Désactivez-le plutôt que de le supprimer."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )


def _student_profile_queryset():
    return Student.objects.prefetch_related(
        "guardian_links__guardian",
        Prefetch(
            "enrollments",
            queryset=Enrollment.objects.filter(
                academic_year__is_active=True,
            ).select_related("classroom", "academic_year"),
            to_attr="active_enrollments",
        ),
    )


class StudentListCreateView(TenantScopedListCreateView):
    queryset = _student_profile_queryset()
    serializer_class = StudentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        classroom = self.request.query_params.get("classroom", "").strip()
        academic_year = self.request.query_params.get("academic_year", "").strip()
        gender = self.request.query_params.get("gender", "").strip()
        has_photo = self.request.query_params.get("has_photo", "").strip().lower()

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(matricule__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(guardian_links__guardian__first_name__icontains=search)
                | Q(guardian_links__guardian__last_name__icontains=search)
                | Q(guardian_links__guardian__phone__icontains=search)
            )

        if status_value:
            queryset = queryset.filter(status=status_value)

        if classroom:
            queryset = queryset.filter(
                enrollments__classroom_id=classroom
            )

        if academic_year:
            queryset = queryset.filter(
                enrollments__academic_year_id=academic_year
            )

        if gender:
            queryset = queryset.filter(gender=gender)

        if has_photo in {"1", "true", "yes"}:
            queryset = queryset.exclude(photo__isnull=True).exclude(photo="")
        elif has_photo in {"0", "false", "no"}:
            queryset = queryset.filter(Q(photo__isnull=True) | Q(photo=""))

        return queryset.distinct()


class StudentDetailView(TenantScopedDetailView):
    queryset = _student_profile_queryset()
    serializer_class = StudentSerializer


class StudentPhotoView(APIView):
    permission_classes = [PeopleManagementPermission]
    parser_classes = [MultiPartParser, FormParser]

    def get_student(self, request, pk):
        return _student_profile_queryset().filter(
            school=request.school,
            pk=pk,
        ).first()

    def post(self, request, pk):
        student = self.get_student(request, pk)
        if not student:
            return Response(
                {"detail": "Élève introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        uploaded = request.FILES.get("photo")
        try:
            content, meta = compress_student_photo(uploaded)
        except StudentPhotoError as exc:
            return Response(
                {"photo": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_storage = student.photo.storage if student.photo else None
        old_name = student.photo.name if student.photo else ""

        filename = f"student-{student.id}.webp"
        student.photo.save(filename, content, save=True)

        if old_storage and old_name and old_name != student.photo.name:
            old_storage.delete(old_name)

        data = StudentSerializer(
            student,
            context={"request": request},
        ).data
        data["photo_meta"] = meta
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        return self.post(request, pk)

    def delete(self, request, pk):
        student = self.get_student(request, pk)
        if not student:
            return Response(
                {"detail": "Élève introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if student.photo:
            storage = student.photo.storage
            name = student.photo.name
            student.photo = None
            student.save(update_fields=["photo", "updated_at"])
            if name:
                storage.delete(name)

        return Response(
            StudentSerializer(
                student,
                context={"request": request},
            ).data
        )


class TeacherListCreateView(TenantScopedListCreateView):
    queryset = Teacher.objects.select_related("user").all()
    serializer_class = TeacherSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(employee_number__icontains=search)
                | Q(email__icontains=search)
            )

        return queryset


class TeacherDetailView(TenantScopedDetailView):
    queryset = Teacher.objects.select_related("user").all()
    serializer_class = TeacherSerializer


class GuardianListCreateView(TenantScopedListCreateView):
    queryset = Guardian.objects.select_related("user").prefetch_related(
        "student_links__student",
        Prefetch(
            "student_links__student__enrollments",
            queryset=Enrollment.objects.filter(
                academic_year__is_active=True,
            ).select_related("classroom", "academic_year"),
            to_attr="active_enrollments",
        ),
    ).annotate(
        children_count=Count("student_links", distinct=True)
    )
    serializer_class = GuardianSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(alternate_phone__icontains=search)
                | Q(email__icontains=search)
                | Q(occupation__icontains=search)
                | Q(student_links__student__first_name__icontains=search)
                | Q(student_links__student__last_name__icontains=search)
                | Q(student_links__student__matricule__icontains=search)
            ).distinct()

        return queryset


class GuardianDetailView(TenantScopedDetailView):
    queryset = Guardian.objects.select_related("user").prefetch_related(
        "student_links__student",
        Prefetch(
            "student_links__student__enrollments",
            queryset=Enrollment.objects.filter(
                academic_year__is_active=True,
            ).select_related("classroom", "academic_year"),
            to_attr="active_enrollments",
        ),
    ).annotate(
        children_count=Count("student_links", distinct=True)
    )
    serializer_class = GuardianSerializer


class StudentGuardianListCreateView(TenantScopedListCreateView):
    queryset = StudentGuardian.objects.select_related(
        "student",
        "guardian",
    ).all()
    serializer_class = StudentGuardianSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        student = self.request.query_params.get("student")
        guardian = self.request.query_params.get("guardian")

        if student:
            queryset = queryset.filter(student_id=student)

        if guardian:
            queryset = queryset.filter(guardian_id=guardian)

        return queryset


class StudentGuardianDetailView(TenantScopedDetailView):
    queryset = StudentGuardian.objects.select_related(
        "student",
        "guardian",
    ).all()
    serializer_class = StudentGuardianSerializer


class EnrollmentListCreateView(TenantScopedListCreateView):
    queryset = Enrollment.objects.select_related(
        "student",
        "academic_year",
        "classroom",
        "classroom__level",
        "classroom__level__cycle",
        "classroom__level__cycle__section",
    ).all()
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        student = self.request.query_params.get("student")
        academic_year = self.request.query_params.get("academic_year")
        classroom = self.request.query_params.get("classroom")
        status_value = self.request.query_params.get("status")

        if student:
            queryset = queryset.filter(student_id=student)

        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        if classroom:
            queryset = queryset.filter(classroom_id=classroom)

        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset


class EnrollmentDetailView(TenantScopedDetailView):
    queryset = Enrollment.objects.select_related(
        "student",
        "academic_year",
        "classroom",
        "classroom__level",
        "classroom__level__cycle",
        "classroom__level__cycle__section",
    ).all()
    serializer_class = EnrollmentSerializer


@extend_schema(request=OpenApiTypes.OBJECT, responses={200: OpenApiTypes.OBJECT}, tags=["People"])
@api_view(["GET"])
@permission_classes([PeopleManagementPermission])
def people_summary(request):
    school = request.school

    data = {
        "students": school.students.count(),
        "active_students": school.students.filter(
            status=Student.Status.ACTIVE
        ).count(),
        "teachers": school.teachers.count(),
        "active_teachers": school.teachers.filter(
            status=Teacher.Status.ACTIVE
        ).count(),
        "guardians": school.guardians.filter(is_active=True).count(),
        "enrollments": school.enrollments.count(),
    }

    return Response(PeopleSummarySerializer(data).data)
