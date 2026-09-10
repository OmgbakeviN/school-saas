from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academics.models import AcademicPeriod, AcademicYear, Classroom
from .models import Enrollment, Student
from .operations_serializers import (
    ActionResultSerializer,
    ApplyPromotionRequestSerializer,
    ApplyPromotionResultSerializer,
    BulkClassAssignmentRequestSerializer,
    BulkClassAssignmentResultSerializer,
    ExitStudentsRequestSerializer,
    PeopleImportRequestSerializer,
    PeopleImportResultSerializer,
    PrepareAcademicYearRequestSerializer,
    PrepareAcademicYearResultSerializer,
    PromotionPreviewRequestSerializer,
    PromotionPreviewResultSerializer,
    ReEnrollRepeatersRequestSerializer,
)
from .operations_services import (
    build_export_rows,
    csv_response,
    effective_threshold,
    import_people,
    template_response,
    xlsx_response,
)
from .permissions import PeopleManagementPermission


class BasePeopleImportView(GenericAPIView):
    serializer_class = PeopleImportRequestSerializer
    permission_classes = [PeopleManagementPermission]
    parser_classes = [MultiPartParser, FormParser]
    entity = None

    @extend_schema(
        summary="Importer un fichier CSV/XLSX",
        description=(
            "Import administratif. Pour un import d'élèves, "
            "`academic_year` et `classroom` peuvent être fournis "
            "pour créer l'inscription annuelle dans la même opération."
        ),
        request=PeopleImportRequestSerializer,
        responses={200: PeopleImportResultSerializer},
        tags=["People - Imports"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = import_people(
                request=request,
                entity=self.entity,
                upload=serializer.validated_data["file"],
                dry_run=serializer.validated_data["dry_run"],
                academic_year_id=serializer.validated_data.get(
                    "academic_year"
                ),
                classroom_id=serializer.validated_data.get(
                    "classroom"
                ),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            PeopleImportResultSerializer(result).data
        )


class StudentImportView(BasePeopleImportView):
    entity = "students"


class TeacherImportView(BasePeopleImportView):
    entity = "teachers"


class GuardianImportView(BasePeopleImportView):
    entity = "guardians"


class BaseImportTemplateView(APIView):
    permission_classes = [PeopleManagementPermission]
    entity = None

    @extend_schema(
        summary="Télécharger le modèle CSV d'import",
        responses={(200, "text/csv"): OpenApiTypes.BINARY},
        tags=["People - Imports"],
    )
    def get(self, request, *args, **kwargs):
        return template_response(self.entity)


class StudentImportTemplateView(BaseImportTemplateView):
    entity = "students"


class TeacherImportTemplateView(BaseImportTemplateView):
    entity = "teachers"


class GuardianImportTemplateView(BaseImportTemplateView):
    entity = "guardians"


class BulkClassAssignmentView(GenericAPIView):
    serializer_class = BulkClassAssignmentRequestSerializer
    permission_classes = [PeopleManagementPermission]

    @extend_schema(
        summary="Affecter plusieurs élèves à une classe",
        request=BulkClassAssignmentRequestSerializer,
        responses={200: BulkClassAssignmentResultSerializer},
        tags=["People - Bulk Operations"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        school = request.school
        data = serializer.validated_data

        year = get_object_or_404(
            AcademicYear,
            school=school,
            id=data["academic_year"],
        )
        classroom = get_object_or_404(
            Classroom.objects.select_related("academic_year"),
            school=school,
            id=data["classroom"],
        )

        if classroom.academic_year_id != year.id:
            return Response(
                {
                    "detail": (
                        "La classe n'appartient pas à l'année "
                        "scolaire sélectionnée."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_ids = list(dict.fromkeys(data["student_ids"]))
        students = list(
            Student.objects.filter(
                school=school,
                id__in=requested_ids,
            )
        )

        if len(students) != len(requested_ids):
            return Response(
                {
                    "detail": (
                        "Un ou plusieurs élèves sont introuvables "
                        "dans cet établissement."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = 0
        updated = 0

        for student in students:
            _enrollment, was_created = (
                Enrollment.objects.update_or_create(
                    school=school,
                    student=student,
                    academic_year=year,
                    defaults={
                        "classroom": classroom,
                        "enrollment_date": data.get(
                            "enrollment_date"
                        ),
                        "status": Enrollment.Status.ACTIVE,
                    },
                )
            )

            if was_created:
                created += 1
            else:
                updated += 1

        result = {
            "created": created,
            "updated": updated,
            "total": len(students),
        }

        return Response(
            BulkClassAssignmentResultSerializer(result).data
        )


class PromotionPreviewView(GenericAPIView):
    serializer_class = PromotionPreviewRequestSerializer
    permission_classes = [PeopleManagementPermission]

    @extend_schema(
        summary="Prévisualiser les décisions de fin d'année",
        description=(
            "Compare la moyenne annuelle au seuil effectif "
            "niveau → cycle → établissement. "
            "La proposition reste modifiable par la direction."
        ),
        request=PromotionPreviewRequestSerializer,
        responses={200: PromotionPreviewResultSerializer},
        tags=["People - Promotions"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        school = request.school
        data = serializer.validated_data

        year = get_object_or_404(
            AcademicYear,
            school=school,
            id=data["academic_year"],
        )

        queryset = (
            Enrollment.objects
            .filter(
                school=school,
                academic_year=year,
            )
            .select_related(
                "student",
                "classroom",
                "classroom__level",
                "classroom__level__cycle",
            )
        )

        if data.get("classroom"):
            queryset = queryset.filter(
                classroom_id=data["classroom"]
            )

        items = []

        for enrollment in queryset:
            threshold = effective_threshold(
                enrollment.classroom.level
            )

            if enrollment.final_average is None:
                suggestion = (
                    Enrollment.PromotionDecision.PENDING
                )
            elif enrollment.final_average >= threshold:
                suggestion = (
                    Enrollment.PromotionDecision.PROMOTED
                )
            else:
                suggestion = (
                    Enrollment.PromotionDecision.REPEATED
                )

            items.append({
                "enrollment_id": enrollment.id,
                "student_id": enrollment.student_id,
                "student_name": (
                    f"{enrollment.student.last_name} "
                    f"{enrollment.student.first_name}"
                ).strip(),
                "matricule": enrollment.student.matricule,
                "classroom_id": enrollment.classroom_id,
                "classroom_name": enrollment.classroom.name,
                "level_id": enrollment.classroom.level_id,
                "level_name": enrollment.classroom.level.name,
                "final_average": enrollment.final_average,
                "threshold": threshold,
                "suggested_decision": suggestion,
            })

        result = {
            "academic_year": year.id,
            "count": len(items),
            "items": items,
        }

        return Response(
            PromotionPreviewResultSerializer(result).data
        )


def create_next_enrollment(source, target_classroom):
    return Enrollment.objects.update_or_create(
        school=source.school,
        student=source.student,
        academic_year=target_classroom.academic_year,
        defaults={
            "classroom": target_classroom,
            "status": Enrollment.Status.ACTIVE,
            "promotion_decision": (
                Enrollment.PromotionDecision.PENDING
            ),
        },
    )


class ApplyPromotionsView(GenericAPIView):
    serializer_class = ApplyPromotionRequestSerializer
    permission_classes = [PeopleManagementPermission]

    @extend_schema(
        summary="Appliquer les décisions de fin d'année",
        request=ApplyPromotionRequestSerializer,
        responses={200: ApplyPromotionResultSerializer},
        tags=["People - Promotions"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        counters = {
            "processed": 0,
            "promoted": 0,
            "repeated": 0,
            "graduated": 0,
            "transferred": 0,
            "withdrawn": 0,
            "next_enrollments_created": 0,
            "next_enrollments_updated": 0,
        }

        for item in serializer.validated_data["items"]:
            source = get_object_or_404(
                Enrollment.objects.select_related(
                    "student",
                    "academic_year",
                ),
                school=request.school,
                id=item["enrollment_id"],
            )

            decision = item["decision"]
            reason = item.get("reason", "")
            next_enrollment = None

            if decision in {
                Enrollment.PromotionDecision.PROMOTED,
                Enrollment.PromotionDecision.REPEATED,
            }:
                target_classroom_id = item.get(
                    "target_classroom"
                )

                if not target_classroom_id:
                    return Response(
                        {
                            "detail": (
                                "Une classe de destination est "
                                "obligatoire pour une promotion "
                                "ou un redoublement."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                target_classroom = get_object_or_404(
                    Classroom.objects.select_related(
                        "academic_year",
                        "level",
                    ),
                    school=request.school,
                    id=target_classroom_id,
                )

                if (
                    target_classroom.academic_year_id
                    == source.academic_year_id
                ):
                    return Response(
                        {
                            "detail": (
                                "La classe de destination doit "
                                "appartenir à une autre année scolaire."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                next_enrollment, was_created = (
                    create_next_enrollment(
                        source,
                        target_classroom,
                    )
                )

                if was_created:
                    counters[
                        "next_enrollments_created"
                    ] += 1
                else:
                    counters[
                        "next_enrollments_updated"
                    ] += 1

                source.next_enrollment = next_enrollment
                source.status = Enrollment.Status.COMPLETED

                if (
                    decision
                    == Enrollment.PromotionDecision.PROMOTED
                ):
                    counters["promoted"] += 1
                else:
                    counters["repeated"] += 1

            elif (
                decision
                == Enrollment.PromotionDecision.GRADUATED
            ):
                source.status = Enrollment.Status.COMPLETED
                source.student.status = Student.Status.GRADUATED
                source.student.save(update_fields=["status"])
                counters["graduated"] += 1

            elif (
                decision
                == Enrollment.PromotionDecision.TRANSFERRED
            ):
                source.status = Enrollment.Status.TRANSFERRED
                source.student.status = Student.Status.TRANSFERRED
                source.student.save(update_fields=["status"])
                counters["transferred"] += 1

            elif (
                decision
                == Enrollment.PromotionDecision.WITHDRAWN
            ):
                source.status = Enrollment.Status.WITHDRAWN
                source.student.status = Student.Status.WITHDRAWN
                source.student.save(update_fields=["status"])
                counters["withdrawn"] += 1

            source.promotion_decision = decision
            source.decision_reason = reason
            source.save(
                update_fields=[
                    "status",
                    "promotion_decision",
                    "decision_reason",
                    "next_enrollment",
                    "updated_at",
                ]
            )

            counters["processed"] += 1

        return Response(
            ApplyPromotionResultSerializer(counters).data
        )


class ReEnrollRepeatersView(GenericAPIView):
    serializer_class = ReEnrollRepeatersRequestSerializer
    permission_classes = [PeopleManagementPermission]

    @extend_schema(
        summary="Réinscrire plusieurs redoublants",
        request=ReEnrollRepeatersRequestSerializer,
        responses={200: ActionResultSerializer},
        tags=["People - Promotions"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_classroom = get_object_or_404(
            Classroom.objects.select_related("academic_year"),
            school=request.school,
            id=serializer.validated_data["target_classroom"],
        )

        source_ids = list(
            dict.fromkeys(
                serializer.validated_data["enrollment_ids"]
            )
        )

        sources = list(
            Enrollment.objects.filter(
                school=request.school,
                id__in=source_ids,
            ).select_related("student", "academic_year")
        )

        if len(sources) != len(source_ids):
            return Response(
                {
                    "detail": (
                        "Une ou plusieurs inscriptions "
                        "sont introuvables."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        processed = 0

        for source in sources:
            if (
                target_classroom.academic_year_id
                == source.academic_year_id
            ):
                return Response(
                    {
                        "detail": (
                            "La classe cible doit appartenir "
                            "à une autre année scolaire."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            next_enrollment, _created = (
                create_next_enrollment(
                    source,
                    target_classroom,
                )
            )

            source.status = Enrollment.Status.COMPLETED
            source.promotion_decision = (
                Enrollment.PromotionDecision.REPEATED
            )
            source.decision_reason = (
                serializer.validated_data.get("reason", "")
            )
            source.next_enrollment = next_enrollment
            source.save()

            processed += 1

        return Response({"processed": processed})


class ExitStudentsView(GenericAPIView):
    serializer_class = ExitStudentsRequestSerializer
    permission_classes = [PeopleManagementPermission]

    @extend_schema(
        summary="Transférer ou retirer plusieurs élèves",
        request=ExitStudentsRequestSerializer,
        responses={200: ActionResultSerializer},
        tags=["People - Promotions"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        reason = serializer.validated_data.get(
            "reason",
            "",
        )
        ids = list(
            dict.fromkeys(
                serializer.validated_data["enrollment_ids"]
            )
        )

        queryset = list(
            Enrollment.objects.filter(
                school=request.school,
                id__in=ids,
            ).select_related("student")
        )

        if len(queryset) != len(ids):
            return Response(
                {
                    "detail": (
                        "Une ou plusieurs inscriptions "
                        "sont introuvables."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment_status = (
            Enrollment.Status.TRANSFERRED
            if (
                action
                == Enrollment.PromotionDecision.TRANSFERRED
            )
            else Enrollment.Status.WITHDRAWN
        )
        student_status = (
            Student.Status.TRANSFERRED
            if (
                action
                == Enrollment.PromotionDecision.TRANSFERRED
            )
            else Student.Status.WITHDRAWN
        )

        for enrollment in queryset:
            enrollment.status = enrollment_status
            enrollment.promotion_decision = action
            enrollment.decision_reason = reason
            enrollment.save()

            enrollment.student.status = student_status
            enrollment.student.save(update_fields=["status"])

        return Response({"processed": len(queryset)})


class PrepareAcademicYearView(GenericAPIView):
    serializer_class = PrepareAcademicYearRequestSerializer
    permission_classes = [PeopleManagementPermission]

    @extend_schema(
        summary="Préparer une nouvelle année scolaire",
        description=(
            "Crée une nouvelle année et peut recopier "
            "les classes et les périodes de l'année source."
        ),
        request=PrepareAcademicYearRequestSerializer,
        responses={
            201: PrepareAcademicYearResultSerializer
        },
        tags=["People - Academic Year Transition"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        school = request.school

        source = get_object_or_404(
            AcademicYear,
            school=school,
            id=data["source_academic_year"],
        )

        if AcademicYear.objects.filter(
            school=school,
            name=data["name"],
        ).exists():
            return Response(
                {
                    "detail": (
                        "Une année scolaire portant ce nom "
                        "existe déjà."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data["is_active"]:
            AcademicYear.objects.filter(
                school=school,
                is_active=True,
            ).update(is_active=False)

        target = AcademicYear.objects.create(
            school=school,
            name=data["name"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            period_system=data.get(
                "period_system",
                source.period_system,
            ),
            is_active=data["is_active"],
        )

        classrooms_created = 0
        periods_created = 0

        if data["clone_classrooms"]:
            for classroom in source.classrooms.all():
                Classroom.objects.create(
                    school=school,
                    academic_year=target,
                    level=classroom.level,
                    name=classroom.name,
                    code=classroom.code,
                    capacity=classroom.capacity,
                    order=classroom.order,
                    is_active=classroom.is_active,
                )
                classrooms_created += 1

        if data["clone_periods"]:
            for period in source.periods.all():
                AcademicPeriod.objects.create(
                    school=school,
                    academic_year=target,
                    name=period.name,
                    code=period.code,
                    kind=period.kind,
                    order=period.order,
                    weight=period.weight,
                    start_date=None,
                    end_date=None,
                    is_active=period.is_active,
                )
                periods_created += 1

        result = {
            "academic_year_id": target.id,
            "academic_year_name": target.name,
            "classrooms_created": classrooms_created,
            "periods_created": periods_created,
        }

        return Response(
            PrepareAcademicYearResultSerializer(result).data,
            status=status.HTTP_201_CREATED,
        )


class BasePeopleExportView(APIView):
    permission_classes = [PeopleManagementPermission]
    entity = None

    @extend_schema(
        summary="Exporter une liste",
        parameters=[
            OpenApiParameter(
                name="file_format",
                type=str,
                enum=["csv", "xlsx"],
                default="xlsx",
                description=(
                    "Format du fichier exporté. "
                    "Utiliser `file_format` plutôt que le paramètre DRF réservé `format`."
                ),
            ),
            OpenApiParameter(
                name="academic_year",
                type=int,
                required=False,
            ),
            OpenApiParameter(
                name="classroom",
                type=int,
                required=False,
            ),
        ],
        responses={
            (200, "text/csv"): OpenApiTypes.BINARY,
            (
                200,
                (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            ): OpenApiTypes.BINARY,
        },
        tags=["People - Exports"],
    )
    def get(self, request, *args, **kwargs):
        export_format = (
            request.query_params.get("file_format")
            or request.query_params.get("format")
            or "xlsx"
        ).lower()

        if export_format not in {"csv", "xlsx"}:
            return Response(
                {"detail": "Format d'export invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        academic_year_id = request.query_params.get(
            "academic_year"
        )
        classroom_id = request.query_params.get("classroom")

        headers, rows = build_export_rows(
            self.entity,
            request.school,
            academic_year_id=(
                academic_year_id or None
            ),
            classroom_id=classroom_id or None,
        )

        filename = (
            f"{request.school.slug}-{self.entity}"
        )

        if export_format == "csv":
            return csv_response(
                filename,
                headers,
                rows,
            )

        return xlsx_response(
            filename,
            headers,
            rows,
        )


class StudentExportView(BasePeopleExportView):
    entity = "students"


class TeacherExportView(BasePeopleExportView):
    entity = "teachers"


class GuardianExportView(BasePeopleExportView):
    entity = "guardians"


class EnrollmentExportView(BasePeopleExportView):
    entity = "enrollments"
