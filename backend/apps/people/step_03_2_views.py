from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.academics.models import AcademicPeriod, AcademicYear, Classroom
from .models import Enrollment, Student
from .permissions import PeopleManagementPermission
from .step_03_2_serializers import (
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
from .step_03_2_services import (
    build_export_rows,
    csv_response,
    effective_threshold,
    import_people,
    template_response,
    xlsx_response,
)


@extend_schema(
    summary="Importer des élèves, enseignants ou parents/tuteurs",
    description=(
        "Import CSV/XLSX. Pour les élèves, `academic_year` et `classroom` "
        "peuvent être fournis pour les inscrire directement."
    ),
    request=PeopleImportRequestSerializer,
    responses={200: PeopleImportResultSerializer},
    tags=["People - Bulk Operations"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
@parser_classes([MultiPartParser, FormParser])
def import_people_file(request, entity):
    if entity not in {"students", "teachers", "guardians"}:
        return Response(
            {"detail": "Type d'import inconnu."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = PeopleImportRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        result = import_people(
            request=request,
            entity=entity,
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

    return Response(PeopleImportResultSerializer(result).data)


@extend_schema(
    summary="Télécharger un modèle CSV d'import",
    responses={(200, "text/csv"): OpenApiTypes.BINARY},
    tags=["People - Bulk Operations"],
)
@api_view(["GET"])
@permission_classes([PeopleManagementPermission])
def download_import_template(request, entity):
    try:
        return template_response(entity)
    except ValueError as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )


@extend_schema(
    summary="Affecter plusieurs élèves à une classe",
    request=BulkClassAssignmentRequestSerializer,
    responses={200: BulkClassAssignmentResultSerializer},
    tags=["People - Bulk Operations"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
@transaction.atomic
def bulk_assign_class(request):
    serializer = BulkClassAssignmentRequestSerializer(
        data=request.data
    )
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
                    "La classe n'appartient pas à l'année scolaire "
                    "sélectionnée."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    students = list(
        Student.objects.filter(
            school=school,
            id__in=data["student_ids"],
        )
    )

    if len(students) != len(set(data["student_ids"])):
        return Response(
            {"detail": "Un ou plusieurs élèves sont introuvables."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created = 0
    updated = 0

    for student in students:
        _enrollment, was_created = Enrollment.objects.update_or_create(
            school=school,
            student=student,
            academic_year=year,
            defaults={
                "classroom": classroom,
                "enrollment_date": data.get("enrollment_date"),
                "status": Enrollment.Status.ACTIVE,
            },
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


@extend_schema(
    summary="Prévisualiser les décisions de fin d'année",
    description=(
        "Compare la moyenne annuelle déjà disponible au seuil effectif "
        "niveau → cycle → établissement. Sans moyenne, la suggestion reste PENDING."
    ),
    request=PromotionPreviewRequestSerializer,
    responses={200: PromotionPreviewResultSerializer},
    tags=["People - Promotions"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
def promotion_preview(request):
    serializer = PromotionPreviewRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    school = request.school
    data = serializer.validated_data

    year = get_object_or_404(
        AcademicYear,
        school=school,
        id=data["academic_year"],
    )

    queryset = Enrollment.objects.filter(
        school=school,
        academic_year=year,
    ).select_related(
        "student",
        "classroom",
        "classroom__level",
        "classroom__level__cycle",
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
            suggestion = Enrollment.PromotionDecision.PENDING
        elif enrollment.final_average >= threshold:
            suggestion = Enrollment.PromotionDecision.PROMOTED
        else:
            suggestion = Enrollment.PromotionDecision.REPEATED

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


def _create_next_enrollment(
    *,
    source,
    target_classroom,
):
    target_year = target_classroom.academic_year

    return Enrollment.objects.update_or_create(
        school=source.school,
        student=source.student,
        academic_year=target_year,
        defaults={
            "classroom": target_classroom,
            "status": Enrollment.Status.ACTIVE,
            "promotion_decision": Enrollment.PromotionDecision.PENDING,
        },
    )


@extend_schema(
    summary="Appliquer les décisions de fin d'année",
    description=(
        "PROMOTED et REPEATED créent/réutilisent l'inscription de l'année "
        "cible via `target_classroom`. TRANSFERRED/WITHDRAWN/GRADUATED "
        "mettent à jour le statut de l'élève."
    ),
    request=ApplyPromotionRequestSerializer,
    responses={200: ApplyPromotionResultSerializer},
    tags=["People - Promotions"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
@transaction.atomic
def apply_promotions(request):
    serializer = ApplyPromotionRequestSerializer(
        data=request.data
    )
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
            target_classroom_id = item.get("target_classroom")

            if not target_classroom_id:
                return Response(
                    {
                        "detail": (
                            "Une classe de destination est obligatoire "
                            "pour une promotion ou un redoublement."
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

            if target_classroom.academic_year_id == source.academic_year_id:
                return Response(
                    {
                        "detail": (
                            "La classe de destination doit appartenir "
                            "à une autre année scolaire."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            next_enrollment, was_created = _create_next_enrollment(
                source=source,
                target_classroom=target_classroom,
            )

            if was_created:
                counters["next_enrollments_created"] += 1
            else:
                counters["next_enrollments_updated"] += 1

            source.next_enrollment = next_enrollment
            source.status = Enrollment.Status.COMPLETED

            if decision == Enrollment.PromotionDecision.PROMOTED:
                counters["promoted"] += 1
            else:
                counters["repeated"] += 1

        elif decision == Enrollment.PromotionDecision.GRADUATED:
            source.status = Enrollment.Status.COMPLETED
            source.student.status = Student.Status.GRADUATED
            source.student.save(update_fields=["status"])
            counters["graduated"] += 1

        elif decision == Enrollment.PromotionDecision.TRANSFERRED:
            source.status = Enrollment.Status.TRANSFERRED
            source.student.status = Student.Status.TRANSFERRED
            source.student.save(update_fields=["status"])
            counters["transferred"] += 1

        elif decision == Enrollment.PromotionDecision.WITHDRAWN:
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


@extend_schema(
    summary="Réinscrire des redoublants",
    request=ReEnrollRepeatersRequestSerializer,
    responses={200: ActionResultSerializer},
    tags=["People - Promotions"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
@transaction.atomic
def re_enroll_repeaters(request):
    serializer = ReEnrollRepeatersRequestSerializer(
        data=request.data
    )
    serializer.is_valid(raise_exception=True)

    target_classroom = get_object_or_404(
        Classroom.objects.select_related("academic_year"),
        school=request.school,
        id=serializer.validated_data["target_classroom"],
    )

    processed = 0

    for enrollment_id in serializer.validated_data[
        "enrollment_ids"
    ]:
        source = get_object_or_404(
            Enrollment,
            school=request.school,
            id=enrollment_id,
        )

        if target_classroom.academic_year_id == source.academic_year_id:
            return Response(
                {
                    "detail": (
                        "La classe cible doit appartenir à l'année suivante."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        next_enrollment, _created = _create_next_enrollment(
            source=source,
            target_classroom=target_classroom,
        )

        source.status = Enrollment.Status.COMPLETED
        source.promotion_decision = (
            Enrollment.PromotionDecision.REPEATED
        )
        source.decision_reason = serializer.validated_data.get(
            "reason",
            "",
        )
        source.next_enrollment = next_enrollment
        source.save()

        processed += 1

    return Response({"processed": processed})


@extend_schema(
    summary="Transférer ou retirer plusieurs élèves",
    request=ExitStudentsRequestSerializer,
    responses={200: ActionResultSerializer},
    tags=["People - Promotions"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
@transaction.atomic
def bulk_exit_students(request):
    serializer = ExitStudentsRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    action = serializer.validated_data["action"]
    reason = serializer.validated_data.get("reason", "")

    enrollment_status = (
        Enrollment.Status.TRANSFERRED
        if action == Enrollment.PromotionDecision.TRANSFERRED
        else Enrollment.Status.WITHDRAWN
    )
    student_status = (
        Student.Status.TRANSFERRED
        if action == Enrollment.PromotionDecision.TRANSFERRED
        else Student.Status.WITHDRAWN
    )

    queryset = Enrollment.objects.filter(
        school=request.school,
        id__in=serializer.validated_data["enrollment_ids"],
    ).select_related("student")

    processed = 0

    for enrollment in queryset:
        enrollment.status = enrollment_status
        enrollment.promotion_decision = action
        enrollment.decision_reason = reason
        enrollment.save()

        enrollment.student.status = student_status
        enrollment.student.save(update_fields=["status"])

        processed += 1

    return Response({"processed": processed})


@extend_schema(
    summary="Préparer la nouvelle année scolaire",
    description=(
        "Crée une nouvelle année et peut cloner les classes et périodes "
        "de l'année source. Les matières par niveau ne sont pas dupliquées "
        "car elles sont persistantes."
    ),
    request=PrepareAcademicYearRequestSerializer,
    responses={201: PrepareAcademicYearResultSerializer},
    tags=["People - Academic Year Transition"],
)
@api_view(["POST"])
@permission_classes([PeopleManagementPermission])
@transaction.atomic
def prepare_academic_year(request):
    serializer = PrepareAcademicYearRequestSerializer(
        data=request.data
    )
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
                    "Une année scolaire portant ce nom existe déjà."
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


@extend_schema(
    summary="Exporter une liste",
    parameters=[
        OpenApiParameter(
            name="format",
            type=str,
            enum=["csv", "xlsx"],
            default="csv",
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
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ): OpenApiTypes.BINARY,
    },
    tags=["People - Bulk Operations"],
)
@api_view(["GET"])
@permission_classes([PeopleManagementPermission])
def export_people_list(request, entity):
    if entity not in {
        "students",
        "teachers",
        "guardians",
        "enrollments",
    }:
        return Response(
            {"detail": "Type d'export inconnu."},
            status=status.HTTP_404_NOT_FOUND,
        )

    export_format = request.query_params.get(
        "format",
        "csv",
    ).lower()

    if export_format not in {"csv", "xlsx"}:
        return Response(
            {"detail": "Format d'export invalide."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    academic_year_id = request.query_params.get("academic_year")
    classroom_id = request.query_params.get("classroom")

    headers, rows = build_export_rows(
        entity,
        request.school,
        academic_year_id=academic_year_id or None,
        classroom_id=classroom_id or None,
    )

    filename = f"{request.school.slug}-{entity}"

    if export_format == "xlsx":
        return xlsx_response(filename, headers, rows)

    return csv_response(filename, headers, rows)
