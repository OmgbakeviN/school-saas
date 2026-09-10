from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership
from apps.academics.models import AcademicPeriod, AcademicYear, Classroom
from apps.people.models import Enrollment
from apps.teaching.models import TeachingAssignment
from apps.teaching.services import get_teacher_profile_for_user

from .models import Assessment, AssessmentPeriodControl, Grade
from .permissions import (
    CanManageAssessments,
    CanUseAssessments,
    IsAssessmentDirection,
)
from .serializers import (
    AssessmentActionResultSerializer,
    AssessmentPeriodControlSerializer,
    AssessmentSerializer,
    ClassroomPeriodResultSerializer,
    GradeBulkRequestSerializer,
    GradebookSerializer,
    RecalculateYearResultSerializer,
)
from .services import (
    calculate_period_result,
    can_edit_gradebook,
    can_view_assessment,
    get_period_control,
    incomplete_grade_count,
    recalculate_year_averages,
    teacher_can_work_on_assessment,
    user_is_assessment_manager,
)


class AssessmentPeriodControlListView(APIView):
    permission_classes = [IsAuthenticated, CanUseAssessments]

    @extend_schema(
        summary="Périodes de saisie des notes",
        responses={200: AssessmentPeriodControlSerializer(many=True)},
        tags=["Assessments"],
    )
    def get(self, request):
        periods = AcademicPeriod.objects.filter(
            school=request.school,
        ).select_related("academic_year").order_by(
            "-academic_year__start_date",
            "order",
        )

        controls = []
        for period in periods:
            control, _ = AssessmentPeriodControl.objects.get_or_create(
                school=request.school,
                academic_period=period,
            )
            controls.append(control)

        return Response(
            AssessmentPeriodControlSerializer(
                controls,
                many=True,
                context={"request": request},
            ).data
        )


class AssessmentPeriodControlDetailView(APIView):
    permission_classes = [IsAuthenticated, CanManageAssessments]

    @extend_schema(
        summary="Ouvrir ou fermer une période de saisie",
        request=AssessmentPeriodControlSerializer,
        responses={200: AssessmentPeriodControlSerializer},
        tags=["Assessments"],
    )
    def patch(self, request, period_id):
        period = get_object_or_404(
            AcademicPeriod,
            school=request.school,
            id=period_id,
        )
        control = get_period_control(
            school=request.school,
            academic_period=period,
        )

        serializer = AssessmentPeriodControlSerializer(
            control,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        control.score_entry_open = serializer.validated_data.get(
            "score_entry_open",
            control.score_entry_open,
        )
        control.opened_by = request.user
        control.save(update_fields=[
            "score_entry_open",
            "opened_by",
            "updated_at",
        ])
        return Response(
            AssessmentPeriodControlSerializer(
                control,
                context={"request": request},
            ).data
        )


class AssessmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated, CanUseAssessments]

    def get_queryset(self):
        queryset = Assessment.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_period",
            "academic_period__academic_year",
            "teaching_assignment",
            "teaching_assignment__academic_year",
            "teaching_assignment__teacher",
            "teaching_assignment__subject",
            "teaching_assignment__classroom",
            "teaching_assignment__classroom__level",
        ).prefetch_related("grades")

        membership = get_school_membership(self.request)
        if membership and membership.role == SchoolMembership.Role.TEACHER:
            teacher = get_teacher_profile_for_user(
                user=self.request.user,
                school=self.request.school,
            )
            if not teacher:
                return queryset.none()
            queryset = queryset.filter(teaching_assignment__teacher=teacher)

        filters = {
            "teaching_assignment__academic_year_id": self.request.query_params.get("academic_year"),
            "academic_period_id": self.request.query_params.get("period"),
            "teaching_assignment__classroom_id": self.request.query_params.get("classroom"),
            "teaching_assignment__subject_id": self.request.query_params.get("subject"),
            "status": self.request.query_params.get("status"),
        }
        for field, value in filters.items():
            if value:
                queryset = queryset.filter(**{field: value})

        return queryset

    def perform_create(self, serializer):
        serializer.save()


class AssessmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated, CanUseAssessments]

    def get_queryset(self):
        queryset = Assessment.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_period",
            "academic_period__academic_year",
            "teaching_assignment",
            "teaching_assignment__academic_year",
            "teaching_assignment__teacher",
            "teaching_assignment__subject",
            "teaching_assignment__classroom",
            "teaching_assignment__classroom__level",
        ).prefetch_related("grades")

        membership = get_school_membership(self.request)
        if membership and membership.role == SchoolMembership.Role.TEACHER:
            teacher = get_teacher_profile_for_user(
                user=self.request.user,
                school=self.request.school,
            )
            if not teacher:
                return queryset.none()
            queryset = queryset.filter(teaching_assignment__teacher=teacher)

        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not can_view_assessment(request=request, assessment=instance):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if instance.status != Assessment.Status.DRAFT:
            return Response(
                {"detail": "Seul un brouillon peut être supprimé."},
                status=status.HTTP_409_CONFLICT,
            )
        if instance.grades.exists():
            return Response(
                {"detail": "Cette évaluation contient déjà des notes."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)


class GradebookView(APIView):
    permission_classes = [IsAuthenticated, CanUseAssessments]

    def get_assessment(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment.objects.select_related(
                "academic_period",
                "teaching_assignment",
                "teaching_assignment__academic_year",
                "teaching_assignment__teacher",
                "teaching_assignment__subject",
                "teaching_assignment__classroom",
                "teaching_assignment__classroom__level",
            ),
            school=request.school,
            id=assessment_id,
        )
        if not can_view_assessment(request=request, assessment=assessment):
            return None
        return assessment

    def gradebook_payload(self, request, assessment):
        enrollments = Enrollment.objects.filter(
            school=request.school,
            academic_year=assessment.teaching_assignment.academic_year,
            classroom=assessment.teaching_assignment.classroom,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related("student").order_by(
            "student__last_name",
            "student__first_name",
        )

        grades = {
            grade.enrollment_id: grade
            for grade in Grade.objects.filter(
                school=request.school,
                assessment=assessment,
                enrollment__in=enrollments,
            )
        }

        rows = []
        for enrollment in enrollments:
            grade = grades.get(enrollment.id)
            rows.append({
                "enrollment_id": enrollment.id,
                "student_id": enrollment.student_id,
                "matricule": enrollment.student.matricule,
                "student_name": (
                    f"{enrollment.student.last_name} "
                    f"{enrollment.student.first_name}"
                ).strip(),
                "score": grade.score if grade else None,
                "is_absent": grade.is_absent if grade else False,
                "is_exempt": grade.is_exempt if grade else False,
                "comment": grade.comment if grade else "",
            })

        return {
            "assessment": AssessmentSerializer(
                assessment,
                context={"request": request},
            ).data,
            "can_edit": can_edit_gradebook(
                request=request,
                assessment=assessment,
            ),
            "rows": rows,
        }

    @extend_schema(
        summary="Charger le carnet de notes d'une évaluation",
        responses={200: GradebookSerializer},
        tags=["Assessments"],
    )
    def get(self, request, assessment_id):
        assessment = self.get_assessment(request, assessment_id)
        if not assessment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(self.gradebook_payload(request, assessment))

    @extend_schema(
        summary="Enregistrer les notes d'une évaluation",
        request=GradeBulkRequestSerializer,
        responses={200: GradebookSerializer},
        tags=["Assessments"],
    )
    @transaction.atomic
    def put(self, request, assessment_id):
        assessment = self.get_assessment(request, assessment_id)
        if not assessment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not can_edit_gradebook(request=request, assessment=assessment):
            return Response(
                {
                    "detail": (
                        "La saisie est fermée ou votre affectation ne vous autorise pas à saisir ces notes."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GradeBulkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        valid_enrollments = {
            enrollment.id: enrollment
            for enrollment in Enrollment.objects.filter(
                school=request.school,
                academic_year=assessment.teaching_assignment.academic_year,
                classroom=assessment.teaching_assignment.classroom,
                status__in=[
                    Enrollment.Status.ACTIVE,
                    Enrollment.Status.COMPLETED,
                ],
                id__in=[
                    row["enrollment"]
                    for row in serializer.validated_data["grades"]
                ],
            ).select_related("student")
        }

        for row in serializer.validated_data["grades"]:
            enrollment = valid_enrollments.get(row["enrollment"])
            if not enrollment:
                return Response(
                    {"detail": "Une inscription ne correspond pas à cette classe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            score = row.get("score")
            if (
                score is not None
                and (score < 0 or score > assessment.max_score)
            ):
                return Response(
                    {
                        "detail": (
                            f"La note de {enrollment.student} doit être comprise entre 0 et {assessment.max_score}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Grade.objects.update_or_create(
                school=request.school,
                assessment=assessment,
                enrollment=enrollment,
                defaults={
                    "score": None
                    if row.get("is_absent") or row.get("is_exempt")
                    else score,
                    "is_absent": row.get("is_absent", False),
                    "is_exempt": row.get("is_exempt", False),
                    "comment": row.get("comment", ""),
                    "entered_by": request.user,
                },
            )

        return Response(self.gradebook_payload(request, assessment))


class AssessmentOpenView(APIView):
    permission_classes = [IsAuthenticated, CanUseAssessments]

    @extend_schema(
        summary="Ouvrir la saisie d'une évaluation",
        responses={200: AssessmentActionResultSerializer},
        tags=["Assessments"],
    )
    def post(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment.objects.select_related(
                "academic_period",
                "teaching_assignment",
            ),
            school=request.school,
            id=assessment_id,
        )
        if not can_view_assessment(request=request, assessment=assessment):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if assessment.status != Assessment.Status.DRAFT:
            return Response(
                {"detail": "Seul un brouillon peut être ouvert."},
                status=status.HTTP_409_CONFLICT,
            )

        if not user_is_assessment_manager(request) and not teacher_can_work_on_assessment(
            user=request.user,
            school=request.school,
            assessment=assessment,
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        control = get_period_control(
            school=request.school,
            academic_period=assessment.academic_period,
        )
        if not control.score_entry_open:
            return Response(
                {
                    "detail": (
                        "La période de saisie est fermée. L'administration doit d'abord l'ouvrir."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        assessment.status = Assessment.Status.INPUT
        assessment.save(update_fields=["status", "updated_at"])
        return Response({
            "id": assessment.id,
            "status": assessment.status,
            "detail": "Saisie ouverte.",
        })


class AssessmentSubmitView(APIView):
    permission_classes = [IsAuthenticated, CanUseAssessments]

    @extend_schema(
        summary="Soumettre une évaluation à la direction",
        responses={200: AssessmentActionResultSerializer},
        tags=["Assessments"],
    )
    def post(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment.objects.select_related("teaching_assignment"),
            school=request.school,
            id=assessment_id,
        )
        if not can_view_assessment(request=request, assessment=assessment):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if assessment.status != Assessment.Status.INPUT:
            return Response(
                {"detail": "L'évaluation doit être en saisie avant soumission."},
                status=status.HTTP_409_CONFLICT,
            )

        if not user_is_assessment_manager(request) and not teacher_can_work_on_assessment(
            user=request.user,
            school=request.school,
            assessment=assessment,
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        missing = incomplete_grade_count(assessment)
        if missing:
            return Response(
                {
                    "detail": (
                        f"{missing} élève(s) n'ont ni note, ni absence, ni dispense."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        assessment.status = Assessment.Status.SUBMITTED
        assessment.submitted_at = timezone.now()
        assessment.save(update_fields=[
            "status",
            "submitted_at",
            "updated_at",
        ])
        return Response({
            "id": assessment.id,
            "status": assessment.status,
            "detail": "Évaluation soumise à la direction.",
        })


class AssessmentValidateView(APIView):
    permission_classes = [IsAuthenticated, IsAssessmentDirection]

    @extend_schema(
        summary="Valider une évaluation soumise",
        responses={200: AssessmentActionResultSerializer},
        tags=["Assessments"],
    )
    def post(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment,
            school=request.school,
            id=assessment_id,
        )
        if assessment.status != Assessment.Status.SUBMITTED:
            return Response(
                {"detail": "Seule une évaluation soumise peut être validée."},
                status=status.HTTP_409_CONFLICT,
            )

        assessment.status = Assessment.Status.VALIDATED
        assessment.validated_by = request.user
        assessment.validated_at = timezone.now()
        assessment.save(update_fields=[
            "status",
            "validated_by",
            "validated_at",
            "updated_at",
        ])
        return Response({
            "id": assessment.id,
            "status": assessment.status,
            "detail": "Évaluation validée.",
        })


class AssessmentPublishView(APIView):
    permission_classes = [IsAuthenticated, IsAssessmentDirection]

    @extend_schema(
        summary="Publier et verrouiller une évaluation",
        responses={200: AssessmentActionResultSerializer},
        tags=["Assessments"],
    )
    def post(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment,
            school=request.school,
            id=assessment_id,
        )
        if assessment.status != Assessment.Status.VALIDATED:
            return Response(
                {"detail": "Seule une évaluation validée peut être publiée."},
                status=status.HTTP_409_CONFLICT,
            )

        assessment.status = Assessment.Status.PUBLISHED
        assessment.published_by = request.user
        assessment.published_at = timezone.now()
        assessment.save(update_fields=[
            "status",
            "published_by",
            "published_at",
            "updated_at",
        ])
        return Response({
            "id": assessment.id,
            "status": assessment.status,
            "detail": "Évaluation publiée et verrouillée.",
        })


class AssessmentReopenView(APIView):
    permission_classes = [IsAuthenticated, IsAssessmentDirection]

    @extend_schema(
        summary="Rouvrir une évaluation verrouillée",
        responses={200: AssessmentActionResultSerializer},
        tags=["Assessments"],
    )
    def post(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment,
            school=request.school,
            id=assessment_id,
        )
        if assessment.status not in {
            Assessment.Status.SUBMITTED,
            Assessment.Status.VALIDATED,
            Assessment.Status.PUBLISHED,
        }:
            return Response(
                {"detail": "Cette évaluation n'a pas besoin d'être rouverte."},
                status=status.HTTP_409_CONFLICT,
            )

        assessment.status = Assessment.Status.INPUT
        assessment.reopened_by = request.user
        assessment.reopened_at = timezone.now()
        assessment.save(update_fields=[
            "status",
            "reopened_by",
            "reopened_at",
            "updated_at",
        ])
        return Response({
            "id": assessment.id,
            "status": assessment.status,
            "detail": "Évaluation rouverte pour correction.",
        })


class ClassroomPeriodResultsView(APIView):
    permission_classes = [IsAuthenticated, CanManageAssessments]

    @extend_schema(
        summary="Résultats calculés d'une classe pour une période",
        responses={200: ClassroomPeriodResultSerializer},
        tags=["Assessments"],
    )
    def get(self, request, classroom_id, period_id):
        classroom = get_object_or_404(
            Classroom.objects.select_related(
                "academic_year",
                "level",
                "level__cycle",
            ),
            school=request.school,
            id=classroom_id,
        )
        period = get_object_or_404(
            AcademicPeriod,
            school=request.school,
            id=period_id,
            academic_year=classroom.academic_year,
        )

        enrollments = Enrollment.objects.filter(
            school=request.school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related(
            "student",
            "academic_year",
            "classroom",
            "classroom__level",
            "classroom__level__cycle",
        ).order_by("student__last_name", "student__first_name")

        students = []
        for enrollment in enrollments:
            result = calculate_period_result(
                enrollment=enrollment,
                academic_period=period,
            )
            students.append({
                "enrollment_id": enrollment.id,
                "student_id": enrollment.student_id,
                "matricule": enrollment.student.matricule,
                "student_name": (
                    f"{enrollment.student.last_name} "
                    f"{enrollment.student.first_name}"
                ).strip(),
                "subjects": result["subjects"],
                "overall_average": result["overall_average"],
            })

        payload = {
            "classroom_id": classroom.id,
            "classroom_name": classroom.name,
            "period_id": period.id,
            "period_name": period.name,
            "students": students,
        }
        return Response(payload)


class RecalculateYearAveragesView(APIView):
    permission_classes = [IsAuthenticated, CanManageAssessments]

    @extend_schema(
        summary="Recalculer les moyennes annuelles des inscriptions",
        request=None,
        responses={200: RecalculateYearResultSerializer},
        tags=["Assessments"],
    )
    def post(self, request, year_id):
        academic_year = get_object_or_404(
            AcademicYear,
            school=request.school,
            id=year_id,
        )

        classroom = None
        classroom_id = request.data.get("classroom")
        if classroom_id:
            classroom = get_object_or_404(
                Classroom,
                school=request.school,
                academic_year=academic_year,
                id=classroom_id,
            )

        result = recalculate_year_averages(
            school=request.school,
            academic_year=academic_year,
            classroom=classroom,
        )
        return Response(result)
