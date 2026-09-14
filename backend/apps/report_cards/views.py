from django.http import FileResponse, HttpResponse
from io import BytesIO
import re
import zipfile
from django.shortcuts import get_object_or_404
from django.utils.html import escape
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academics.models import AcademicPeriod, Classroom, Subject
from apps.people.models import Enrollment

from .models import ReportCardSnapshot, ReportCardTemplate
from .permissions import (
    CanConfigureReportCardTemplates,
    CanPublishReportCards,
    CanUseReportCards,
)
from .serializers import (
    BulkPublishReportCardsSerializer,
    BulkPublishResultSerializer,
    ClassroomReportCardsZipSerializer,
    PreviewReportCardSerializer,
    PublishReportCardSerializer,
    ReportCardPublishResultSerializer,
    ReportCardOptionsSerializer,
    ReportCardSnapshotSerializer,
    ReportCardTemplateSerializer,
    SetDefaultTemplateSerializer,
)
from .services import (
    build_options,
    can_view_full_class,
    can_view_subject,
    class_annual_results,
    class_period_results,
    build_preview_report_card,
    latest_snapshots,
    publish_report_card,
    student_annual_result,
    student_period_result,
    subject_period_results,
    teacher_full_report_class_ids,
)


class ReportCardOptionsView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Options disponibles pour l'explorateur de bulletins",
        responses={200: ReportCardOptionsSerializer},
        tags=["Report Cards"],
    )
    def get(self, request):
        return Response(build_options(request=request))


class ReportCardTemplateListCreateView(generics.ListCreateAPIView):
    serializer_class = ReportCardTemplateSerializer
    permission_classes = [
        IsAuthenticated,
        CanConfigureReportCardTemplates,
    ]

    def get_queryset(self):
        return (
            ReportCardTemplate.objects.filter(
                school=self.request.school,
            )
            .select_related("cycle")
            .order_by(
                "cycle__order",
                "-is_default",
                "name",
            )
        )

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "request": self.request,
        }

    @extend_schema(
        summary="Lister / créer les modèles de bulletin",
        tags=["Report Cards"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Créer un modèle de bulletin",
        tags=["Report Cards"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ReportCardTemplateDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ReportCardTemplateSerializer
    permission_classes = [
        IsAuthenticated,
        CanConfigureReportCardTemplates,
    ]

    def get_queryset(self):
        return ReportCardTemplate.objects.filter(
            school=self.request.school,
        ).select_related("cycle")

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "request": self.request,
        }


class ReportCardTemplateSetDefaultView(APIView):
    permission_classes = [
        IsAuthenticated,
        CanConfigureReportCardTemplates,
    ]

    @extend_schema(
        summary="Définir un modèle de bulletin par défaut",
        request=SetDefaultTemplateSerializer,
        responses={200: ReportCardTemplateSerializer},
        tags=["Report Cards"],
    )
    def post(self, request, template_id):
        template = get_object_or_404(
            ReportCardTemplate.objects.select_related("cycle"),
            school=request.school,
            id=template_id,
        )

        serializer = SetDefaultTemplateSerializer(
            data=request.data or {"is_default": True}
        )
        serializer.is_valid(raise_exception=True)

        template.is_default = serializer.validated_data[
            "is_default"
        ]
        template.version += 1
        template.save()

        return Response(
            ReportCardTemplateSerializer(
                template,
                context={"request": request},
            ).data
        )


class ReportCardPreviewPdfView(APIView):
    permission_classes = [
        IsAuthenticated,
        CanPublishReportCards,
    ]

    @extend_schema(
        summary="Prévisualiser un bulletin PDF A4 sans le publier",
        description=(
            "Génère un PDF temporaire portant la mention APERÇU. "
            "Aucun ReportCardSnapshot n'est créé. Si la composition "
            "ne tient pas sur une seule feuille A4, l'API renvoie 409."
        ),
        request=PreviewReportCardSerializer,
        responses={
            (200, "application/pdf"): OpenApiTypes.BINARY,
            409: OpenApiTypes.OBJECT,
        },
        tags=["Report Cards"],
    )
    def post(self, request):
        serializer = PreviewReportCardSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "school",
                "student",
                "academic_year",
                "classroom",
                "classroom__level",
                "classroom__level__cycle",
                "classroom__level__cycle__section",
            ),
            school=request.school,
            id=data["enrollment"],
        )

        period = None
        if data["report_type"] == ReportCardSnapshot.ReportType.PERIOD:
            period = get_object_or_404(
                AcademicPeriod,
                school=request.school,
                id=data["academic_period"],
                academic_year=enrollment.academic_year,
            )

        try:
            payload, render = build_preview_report_card(
                enrollment=enrollment,
                report_type=data["report_type"],
                academic_period=period,
                publisher=request.user,
                general_comment=data.get("general_comment", ""),
                teacher_comment=data.get("teacher_comment", ""),
                subject_comments=data.get("subject_comments", {}),
                template_id=data.get("template"),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        if not render["fits_one_page"]:
            return Response(
                {
                    "detail": (
                        "Ce modèle ne tient pas sur une seule feuille A4 "
                        "avec les données de cet élève. Essayez Compact, "
                        "Secondaire paysage, réduisez l'échelle ou masquez "
                        "certaines colonnes."
                    ),
                    "page_count": render["page_count"],
                    "template": payload.get("template"),
                },
                status=status.HTTP_409_CONFLICT,
            )

        response = HttpResponse(
            render["pdf_bytes"],
            content_type="application/pdf",
        )
        language_code = payload.get("language", {}).get("code", "FR")
        preview_filename = (
            "report-card-preview.pdf"
            if language_code == "EN"
            else "apercu-bulletin.pdf"
        )
        response["Content-Disposition"] = (
            f'inline; filename="{preview_filename}"'
        )
        response["X-Report-Card-Pages"] = str(
            render["page_count"]
        )
        response["X-Report-Card-Fits-A4"] = "true"
        response["X-Report-Card-Template"] = (
            payload.get("template", {}).get("key", "CLASSIC")
        )
        response["X-Report-Card-Orientation"] = render[
            "orientation"
        ]
        response["X-Report-Card-Language"] = language_code
        return response


class ClassroomPeriodResultsView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Résultats d'une classe pour une période",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Report Cards"],
    )
    def get(self, request, classroom_id, period_id):
        classroom = get_object_or_404(
            Classroom.objects.select_related(
                "academic_year",
                "level",
            ),
            school=request.school,
            id=classroom_id,
        )
        if not can_view_full_class(request=request, classroom=classroom):
            return Response(status=status.HTTP_403_FORBIDDEN)

        period = get_object_or_404(
            AcademicPeriod,
            school=request.school,
            id=period_id,
            academic_year=classroom.academic_year,
        )

        return Response(
            class_period_results(
                school=request.school,
                classroom=classroom,
                period=period,
            )
        )


class StudentPeriodResultView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Prévisualiser le bulletin d'un élève pour une période",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Report Cards"],
    )
    def get(self, request, enrollment_id, period_id):
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student",
                "academic_year",
                "classroom",
                "classroom__level",
                "classroom__level__cycle",
                "classroom__level__cycle__section",
            ),
            school=request.school,
            id=enrollment_id,
        )

        if not can_view_full_class(
            request=request,
            classroom=enrollment.classroom,
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        period = get_object_or_404(
            AcademicPeriod,
            school=request.school,
            id=period_id,
            academic_year=enrollment.academic_year,
        )

        result = student_period_result(
            school=request.school,
            enrollment=enrollment,
            period=period,
        )
        if result is None:
            return Response(
                {"detail": "Aucun résultat disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)


class SubjectPeriodResultsView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Résultats d'une matière pour une classe et une période",
        parameters=[
            OpenApiParameter(
                name="classroom",
                type=int,
                required=True,
            )
        ],
        responses={200: OpenApiTypes.OBJECT},
        tags=["Report Cards"],
    )
    def get(self, request, subject_id, period_id):
        classroom_id = request.query_params.get("classroom")
        if not classroom_id:
            return Response(
                {"detail": "Le paramètre classroom est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        classroom = get_object_or_404(
            Classroom.objects.select_related("academic_year"),
            school=request.school,
            id=classroom_id,
        )
        subject = get_object_or_404(
            Subject,
            school=request.school,
            id=subject_id,
        )
        period = get_object_or_404(
            AcademicPeriod,
            school=request.school,
            id=period_id,
            academic_year=classroom.academic_year,
        )

        if not can_view_subject(
            request=request,
            classroom=classroom,
            subject=subject,
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(
            subject_period_results(
                school=request.school,
                classroom=classroom,
                period=period,
                subject=subject,
            )
        )


class ClassroomAnnualResultsView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Résultats annuels d'une classe",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Report Cards"],
    )
    def get(self, request, classroom_id):
        classroom = get_object_or_404(
            Classroom.objects.select_related("academic_year"),
            school=request.school,
            id=classroom_id,
        )
        if not can_view_full_class(request=request, classroom=classroom):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(
            class_annual_results(
                school=request.school,
                classroom=classroom,
            )
        )


class StudentAnnualResultView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Prévisualiser le bulletin annuel d'un élève",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Report Cards"],
    )
    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "student",
                "academic_year",
                "classroom",
                "classroom__level",
                "classroom__level__cycle",
                "classroom__level__cycle__section",
            ),
            school=request.school,
            id=enrollment_id,
        )
        if not can_view_full_class(
            request=request,
            classroom=enrollment.classroom,
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        result = student_annual_result(
            school=request.school,
            enrollment=enrollment,
        )
        if result is None:
            return Response(
                {"detail": "Aucun résultat annuel disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)


class ReportCardSnapshotListView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Lister les bulletins publiés",
        parameters=[
            OpenApiParameter("academic_year", int),
            OpenApiParameter("period", int),
            OpenApiParameter("classroom", int),
            OpenApiParameter("student", int),
            OpenApiParameter(
                "report_type",
                str,
                enum=["PERIOD", "ANNUAL"],
            ),
            OpenApiParameter(
                "latest_only",
                bool,
                default=True,
            ),
        ],
        responses={200: ReportCardSnapshotSerializer(many=True)},
        tags=["Report Cards"],
    )
    def get(self, request):
        queryset = ReportCardSnapshot.objects.filter(
            school=request.school,
        ).select_related(
            "enrollment",
            "enrollment__student",
            "enrollment__classroom",
            "academic_year",
            "academic_period",
        ).order_by("-published_at", "-version")

        filters = {
            "academic_year_id": request.query_params.get("academic_year"),
            "academic_period_id": request.query_params.get("period"),
            "enrollment__classroom_id": request.query_params.get("classroom"),
            "enrollment__student_id": request.query_params.get("student"),
            "report_type": request.query_params.get("report_type"),
        }
        for field, value in filters.items():
            if value:
                queryset = queryset.filter(**{field: value})

        if not (
            request.user.school_memberships.filter(
                school=request.school,
                is_active=True,
                role__in=["OWNER", "DIRECTOR", "MANAGER"],
            ).exists()
        ):
            allowed = teacher_full_report_class_ids(
                school=request.school,
                user=request.user,
            )
            queryset = queryset.filter(
                enrollment__classroom_id__in=allowed
            )

        latest_only = (
            request.query_params.get("latest_only", "true").lower()
            != "false"
        )
        items = latest_snapshots(queryset) if latest_only else list(queryset)

        return Response(
            ReportCardSnapshotSerializer(
                items,
                many=True,
                context={"request": request},
            ).data
        )


class PublishReportCardView(APIView):
    permission_classes = [IsAuthenticated, CanPublishReportCards]

    @extend_schema(
        summary="Publier un bulletin individuel",
        description=(
            "Crée un snapshot immuable uniquement si le contenu du bulletin "
            "a changé. Sans modification, la version actuelle est conservée."
        ),
        request=PublishReportCardSerializer,
        responses={
            200: ReportCardPublishResultSerializer,
            201: ReportCardPublishResultSerializer,
        },
        tags=["Report Cards"],
    )
    def post(self, request):
        serializer = PublishReportCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                "school",
                "student",
                "academic_year",
                "classroom",
                "classroom__level",
                "classroom__level__cycle",
                "classroom__level__cycle__section",
            ),
            school=request.school,
            id=data["enrollment"],
        )

        period = None
        if data["report_type"] == ReportCardSnapshot.ReportType.PERIOD:
            period = get_object_or_404(
                AcademicPeriod,
                school=request.school,
                id=data["academic_period"],
                academic_year=enrollment.academic_year,
            )

        try:
            snapshot, created_new_version = publish_report_card(
                enrollment=enrollment,
                report_type=data["report_type"],
                academic_period=period,
                publisher=request.user,
                general_comment=data.get("general_comment", ""),
                teacher_comment=data.get("teacher_comment", ""),
                subject_comments=data.get("subject_comments", {}),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        response_data = {
            "snapshot": ReportCardSnapshotSerializer(
                snapshot,
                context={"request": request},
            ).data,
            "created_new_version": created_new_version,
            "unchanged": not created_new_version,
        }

        return Response(
            response_data,
            status=(
                status.HTTP_201_CREATED
                if created_new_version
                else status.HTTP_200_OK
            ),
        )


class BulkPublishReportCardsView(APIView):
    permission_classes = [IsAuthenticated, CanPublishReportCards]

    @extend_schema(
        summary="Publier les bulletins de toute une classe",
        description=(
            "Génère un bulletin par élève avec des appréciations automatiques. "
            "Une nouvelle version n'est créée que si le contenu a changé."
        ),
        request=BulkPublishReportCardsSerializer,
        responses={201: BulkPublishResultSerializer},
        tags=["Report Cards"],
    )
    def post(self, request):
        serializer = BulkPublishReportCardsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        classroom = get_object_or_404(
            Classroom.objects.select_related(
                "academic_year",
                "level",
            ),
            school=request.school,
            id=data["classroom"],
        )

        period = None
        if data["report_type"] == ReportCardSnapshot.ReportType.PERIOD:
            period = get_object_or_404(
                AcademicPeriod,
                school=request.school,
                id=data["academic_period"],
                academic_year=classroom.academic_year,
            )

        enrollments = Enrollment.objects.filter(
            school=request.school,
            classroom=classroom,
            academic_year=classroom.academic_year,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related(
            "student",
            "academic_year",
            "classroom__level__cycle__section",
        )

        snapshots = []
        created = 0
        unchanged = 0
        errors = []

        for enrollment in enrollments:
            try:
                snapshot, created_new_version = publish_report_card(
                    enrollment=enrollment,
                    report_type=data["report_type"],
                    academic_period=period,
                    publisher=request.user,
                )
                snapshots.append(snapshot)
                if created_new_version:
                    created += 1
                else:
                    unchanged += 1
            except Exception as exc:
                errors.append({
                    "enrollment": enrollment.id,
                    "student": str(enrollment.student),
                    "detail": str(exc),
                })

        if created:
            response_status = status.HTTP_201_CREATED
        elif snapshots:
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_409_CONFLICT

        return Response(
            {
                "created": created,
                "unchanged": unchanged,
                "failed": len(errors),
                "snapshots": ReportCardSnapshotSerializer(
                    snapshots,
                    many=True,
                    context={"request": request},
                ).data,
                "errors": errors,
            },
            status=response_status,
        )


def _safe_zip_filename(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip())
    value = value.strip("-_.")
    return value or "document"


class ClassroomReportCardsZipView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Télécharger les bulletins publiés d'une classe en ZIP",
        description=(
            "Télécharge la dernière version publiée de chaque élève pour "
            "la classe et le contexte demandés. Un manifest.txt indique les "
            "élèves dont aucun bulletin n'est encore publié."
        ),
        parameters=[
            OpenApiParameter(
                name="classroom",
                type=int,
                required=True,
            ),
            OpenApiParameter(
                name="report_type",
                type=str,
                enum=["PERIOD", "ANNUAL"],
                required=True,
            ),
            OpenApiParameter(
                name="academic_period",
                type=int,
                required=False,
            ),
        ],
        responses={
            (200, "application/zip"): OpenApiTypes.BINARY,
        },
        tags=["Report Cards"],
    )
    def get(self, request):
        serializer = ClassroomReportCardsZipSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        classroom = get_object_or_404(
            Classroom.objects.select_related(
                "academic_year",
                "level",
            ),
            school=request.school,
            id=data["classroom"],
        )

        if not can_view_full_class(
            request=request,
            classroom=classroom,
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        period = None
        if data["report_type"] == ReportCardSnapshot.ReportType.PERIOD:
            period = get_object_or_404(
                AcademicPeriod,
                school=request.school,
                id=data["academic_period"],
                academic_year=classroom.academic_year,
            )

        queryset = ReportCardSnapshot.objects.filter(
            school=request.school,
            enrollment__classroom=classroom,
            enrollment__academic_year=classroom.academic_year,
            report_type=data["report_type"],
        ).select_related(
            "enrollment__student",
            "enrollment__classroom",
            "academic_year",
            "academic_period",
        )

        if period:
            queryset = queryset.filter(academic_period=period)
        else:
            queryset = queryset.filter(academic_period__isnull=True)

        snapshots = latest_snapshots(
            queryset.order_by("-published_at", "-version")
        )

        if not snapshots:
            return Response(
                {
                    "detail": (
                        "Aucun bulletin publié n'est disponible pour cette "
                        "classe et ce contexte."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        published_enrollment_ids = {
            snapshot.enrollment_id
            for snapshot in snapshots
        }

        expected_enrollments = Enrollment.objects.filter(
            school=request.school,
            classroom=classroom,
            academic_year=classroom.academic_year,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related("student").order_by(
            "student__last_name",
            "student__first_name",
        )

        missing = [
            enrollment
            for enrollment in expected_enrollments
            if enrollment.id not in published_enrollment_ids
        ]

        buffer = BytesIO()
        with zipfile.ZipFile(
            buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            used_names = set()

            for snapshot in snapshots:
                student = snapshot.enrollment.student
                base_name = (
                    f"{student.matricule}-"
                    f"{student.last_name}-{student.first_name}-"
                    f"v{snapshot.version}.pdf"
                )
                filename = _safe_zip_filename(base_name)

                counter = 2
                unique_name = filename
                while unique_name in used_names:
                    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
                    unique_name = f"{stem}-{counter}.pdf"
                    counter += 1

                used_names.add(unique_name)

                with snapshot.pdf_file.open("rb") as pdf:
                    archive.writestr(
                        unique_name,
                        pdf.read(),
                    )

            scope = (
                period.name
                if period
                else "Bulletins annuels"
            )
            manifest_lines = [
                "BE WISE School - Export de bulletins",
                f"Établissement : {request.school.name}",
                f"Classe : {classroom.name}",
                f"Année : {classroom.academic_year.name}",
                f"Contexte : {scope}",
                f"Bulletins inclus : {len(snapshots)}",
                f"Élèves sans bulletin publié : {len(missing)}",
                "",
            ]

            if missing:
                manifest_lines.append("ÉLÈVES SANS BULLETIN PUBLIÉ")
                for enrollment in missing:
                    manifest_lines.append(
                        f"- {enrollment.student.matricule} - "
                        f"{enrollment.student.last_name} "
                        f"{enrollment.student.first_name}"
                    )

            archive.writestr(
                "manifest.txt",
                "\\n".join(manifest_lines).encode("utf-8"),
            )

        buffer.seek(0)

        scope_name = (
            _safe_zip_filename(period.name)
            if period
            else "annuel"
        )
        filename = (
            f"bulletins-"
            f"{_safe_zip_filename(classroom.name)}-"
            f"{_safe_zip_filename(classroom.academic_year.name)}-"
            f"{scope_name}.zip"
        )

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/zip",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )
        response["X-Report-Cards-Included"] = str(len(snapshots))
        response["X-Report-Cards-Missing"] = str(len(missing))
        return response


class ReportCardPdfView(APIView):
    permission_classes = [IsAuthenticated, CanUseReportCards]

    @extend_schema(
        summary="Télécharger le PDF officiel d'un bulletin",
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
        tags=["Report Cards"],
    )
    def get(self, request, snapshot_id):
        snapshot = get_object_or_404(
            ReportCardSnapshot.objects.select_related(
                "enrollment__classroom",
            ),
            school=request.school,
            id=snapshot_id,
        )

        if not (
            request.user.school_memberships.filter(
                school=request.school,
                is_active=True,
                role__in=["OWNER", "DIRECTOR", "MANAGER"],
            ).exists()
        ):
            if snapshot.enrollment.classroom_id not in teacher_full_report_class_ids(
                school=request.school,
                user=request.user,
            ):
                return Response(status=status.HTTP_403_FORBIDDEN)

        return FileResponse(
            snapshot.pdf_file.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=snapshot.pdf_file.name.split("/")[-1],
        )


class PublicReportCardVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Vérifier publiquement l'authenticité d'un bulletin",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Report Cards"],
    )
    def get(self, request, token):
        snapshot = get_object_or_404(
            ReportCardSnapshot.objects.select_related(
                "school",
                "enrollment__student",
                "enrollment__classroom",
                "academic_year",
                "academic_period",
            ),
            verification_token=token,
        )

        student = snapshot.enrollment.student
        masked_name = (
            f"{student.first_name} "
            f"{student.last_name[:1].upper()}."
        ).strip()

        return Response({
            "authentic": True,
            "school": {
                "name": snapshot.school.name,
                "acronym": snapshot.school.acronym,
            },
            "student": masked_name,
            "classroom": snapshot.enrollment.classroom.name,
            "academic_year": snapshot.academic_year.name,
            "report_type": snapshot.report_type,
            "period": (
                snapshot.academic_period.name
                if snapshot.academic_period_id
                else None
            ),
            "version": snapshot.version,
            "published_at": snapshot.published_at,
            "fingerprint": snapshot.payload_sha256[:16].upper(),
        })

class PublicReportCardVerificationPageView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        snapshot = get_object_or_404(
            ReportCardSnapshot.objects.select_related(
                "school",
                "enrollment__student",
                "enrollment__classroom",
                "academic_year",
                "academic_period",
            ),
            verification_token=token,
        )

        student = snapshot.enrollment.student
        masked_name = (
            f"{student.first_name} "
            f"{student.last_name[:1].upper()}."
        ).strip()
        period = (
            snapshot.academic_period.name
            if snapshot.academic_period_id
            else "Bulletin annuel"
        )
        fingerprint = snapshot.payload_sha256[:16].upper()

        html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vérification bulletin - {escape(snapshot.school.name)}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #f8fafc;
      color: #0f172a;
      font-family: Arial, Helvetica, sans-serif;
      padding: 24px;
    }}
    .card {{
      width: min(680px, 100%);
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 24px;
      padding: 32px;
      box-shadow: 0 20px 50px rgba(15, 23, 42, .08);
    }}
    .badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 8px 12px;
      background: #ecfdf5;
      color: #047857;
      font-size: 13px;
      font-weight: 700;
    }}
    h1 {{ margin: 18px 0 4px; font-size: 26px; }}
    .muted {{ color: #64748b; }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 24px;
    }}
    .item {{
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 14px;
    }}
    .label {{
      color: #94a3b8;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .value {{ margin-top: 5px; font-weight: 700; }}
    .fingerprint {{
      margin-top: 22px;
      padding: 14px;
      border-radius: 14px;
      background: #f8fafc;
      font-family: monospace;
      font-size: 13px;
    }}
    @media (max-width: 560px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .card {{ padding: 22px; }}
    }}
  </style>
</head>
<body>
  <main class="card">
    <span class="badge">✓ Bulletin authentique</span>
    <h1>{escape(snapshot.school.name)}</h1>
    <div class="muted">Document officiel enregistré dans BE WISE School.</div>

    <div class="grid">
      <div class="item">
        <div class="label">Élève</div>
        <div class="value">{escape(masked_name)}</div>
      </div>
      <div class="item">
        <div class="label">Classe</div>
        <div class="value">{escape(snapshot.enrollment.classroom.name)}</div>
      </div>
      <div class="item">
        <div class="label">Année scolaire</div>
        <div class="value">{escape(snapshot.academic_year.name)}</div>
      </div>
      <div class="item">
        <div class="label">Période</div>
        <div class="value">{escape(period)}</div>
      </div>
      <div class="item">
        <div class="label">Version</div>
        <div class="value">v{snapshot.version}</div>
      </div>
      <div class="item">
        <div class="label">Publié le</div>
        <div class="value">{snapshot.published_at:%d/%m/%Y %H:%M}</div>
      </div>
    </div>

    <div class="fingerprint">
      Empreinte : {fingerprint}
    </div>
  </main>
</body>
</html>"""
        return HttpResponse(html, content_type="text/html; charset=utf-8")

