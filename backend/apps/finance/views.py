from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.academics.models import AcademicYear, Classroom, Level

from .models import (
    StudentTuitionAccount,
    TuitionInstallment,
    TuitionPayment,
    TuitionPlan,
)
from .permissions import CanConfigureFinance, CanUseFinance
from .serializers import (
    BulkAssignPlanSerializer,
    FinanceDashboardSerializer,
    FinanceOptionsSerializer,
    RecordPaymentResultSerializer,
    RecordPaymentSerializer,
    StudentTuitionAccountSerializer,
    TuitionInstallmentSerializer,
    TuitionPaymentSerializer,
    TuitionPlanSerializer,
)
from .services import (
    account_summary,
    assign_plan_to_eligible_students,
    dashboard_summary,
    enrich_account,
    plan_total,
    record_payment,
)


def plan_has_payments(plan):
    return TuitionPayment.objects.filter(
        tuition_account__plan=plan,
    ).exists()


class FinanceOptionsView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Options pour le module pension",
        responses={200: FinanceOptionsSerializer},
        tags=["Finance"],
    )
    def get(self, request):
        years = AcademicYear.objects.filter(
            school=request.school,
        ).order_by("-start_date")

        levels = Level.objects.filter(
            school=request.school,
            is_active=True,
        ).select_related("cycle").order_by(
            "cycle__order",
            "order",
            "name",
        )

        classrooms = Classroom.objects.filter(
            school=request.school,
            is_active=True,
        ).select_related(
            "academic_year",
            "level",
        ).order_by(
            "-academic_year__start_date",
            "level__order",
            "name",
        )

        return Response({
            "years": [
                {
                    "id": item.id,
                    "name": item.name,
                    "is_active": item.is_active,
                }
                for item in years
            ],
            "levels": [
                {
                    "id": item.id,
                    "name": item.name,
                    "cycle_name": item.cycle.name,
                }
                for item in levels
            ],
            "classrooms": [
                {
                    "id": item.id,
                    "name": item.name,
                    "level": item.level_id,
                    "level_name": item.level.name,
                    "academic_year": item.academic_year_id,
                    "academic_year_name": item.academic_year.name,
                }
                for item in classrooms
            ],
        })


class FinanceDashboardView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Tableau de bord pension",
        parameters=[
            OpenApiParameter("academic_year", int),
            OpenApiParameter("classroom", int),
        ],
        responses={200: FinanceDashboardSerializer},
        tags=["Finance"],
    )
    def get(self, request):
        return Response(
            dashboard_summary(
                school=request.school,
                academic_year_id=request.query_params.get(
                    "academic_year"
                ),
                classroom_id=request.query_params.get(
                    "classroom"
                ),
            )
        )


class TuitionPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = TuitionPlanSerializer
    permission_classes = [IsAuthenticated, CanUseFinance]

    def get_permissions(self):
        if self.request.method == "POST":
            return [
                IsAuthenticated(),
                CanConfigureFinance(),
            ]
        return super().get_permissions()

    def get_queryset(self):
        queryset = TuitionPlan.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_year",
            "level",
            "classroom",
        ).prefetch_related("installments")

        year = self.request.query_params.get("academic_year")
        if year:
            queryset = queryset.filter(academic_year_id=year)

        return queryset

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "request": self.request,
        }


class TuitionPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TuitionPlanSerializer
    permission_classes = [IsAuthenticated, CanConfigureFinance]

    def get_queryset(self):
        return TuitionPlan.objects.filter(
            school=self.request.school,
        ).select_related(
            "academic_year",
            "level",
            "classroom",
        ).prefetch_related("installments")

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "request": self.request,
        }

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if plan_has_payments(instance):
            protected = {
                "academic_year",
                "name",
                "currency",
                "level",
                "classroom",
            }
            if protected.intersection(request.data.keys()):
                return Response(
                    {
                        "detail": (
                            "Ce plan possède déjà des paiements. "
                            "Sa structure financière ne peut plus être modifiée."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.student_accounts.exists():
            return Response(
                {
                    "detail": (
                        "Ce plan est déjà affecté à des élèves. "
                        "Désactivez-le au lieu de le supprimer."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return super().destroy(request, *args, **kwargs)


class PlanInstallmentListCreateView(generics.ListCreateAPIView):
    serializer_class = TuitionInstallmentSerializer
    permission_classes = [IsAuthenticated, CanConfigureFinance]

    def get_plan(self):
        return get_object_or_404(
            TuitionPlan,
            school=self.request.school,
            id=self.kwargs["plan_id"],
        )

    def get_queryset(self):
        return TuitionInstallment.objects.filter(
            plan=self.get_plan(),
        )

    def perform_create(self, serializer):
        plan = self.get_plan()

        from rest_framework.exceptions import ValidationError

        if plan_has_payments(plan):
            raise ValidationError(
                "Impossible d'ajouter une tranche après le premier paiement."
            )

        if plan.installments.filter(
            order=serializer.validated_data["order"]
        ).exists():
            raise ValidationError({
                "order": (
                    "Une tranche utilise déjà cet ordre dans ce plan."
                )
            })

        installment = serializer.save(plan=plan)
        installment.full_clean()
        installment.save()


class TuitionInstallmentDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = TuitionInstallmentSerializer
    permission_classes = [IsAuthenticated, CanConfigureFinance]

    def get_queryset(self):
        return TuitionInstallment.objects.filter(
            plan__school=self.request.school,
        ).select_related("plan")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if plan_has_payments(instance.plan):
            return Response(
                {
                    "detail": (
                        "Les tranches sont verrouillées après le premier paiement."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        requested_order = request.data.get("order")
        if (
            requested_order is not None
            and instance.plan.installments.filter(
                order=requested_order
            ).exclude(id=instance.id).exists()
        ):
            return Response(
                {
                    "order": [
                        "Une tranche utilise déjà cet ordre dans ce plan."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if plan_has_payments(instance.plan):
            return Response(
                {
                    "detail": (
                        "Les tranches sont verrouillées après le premier paiement."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return super().destroy(request, *args, **kwargs)


class AssignPlanView(APIView):
    permission_classes = [IsAuthenticated, CanConfigureFinance]

    @extend_schema(
        summary="Créer les comptes pension des élèves éligibles",
        request=BulkAssignPlanSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Finance"],
    )
    def post(self, request, plan_id):
        serializer = BulkAssignPlanSerializer(
            data={"plan": plan_id}
        )
        serializer.is_valid(raise_exception=True)

        plan = get_object_or_404(
            TuitionPlan.objects.prefetch_related("installments"),
            school=request.school,
            id=plan_id,
        )

        if plan_total(plan) <= 0:
            return Response(
                {
                    "detail": (
                        "Ajoutez au moins une tranche active avant "
                        "d'affecter ce plan aux élèves."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            assign_plan_to_eligible_students(plan)
        )


class TuitionAccountListView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Lister les comptes pension des élèves",
        parameters=[
            OpenApiParameter("academic_year", int),
            OpenApiParameter("classroom", int),
            OpenApiParameter(
                "payment_status",
                str,
                enum=["PAID", "PARTIAL", "UNPAID"],
            ),
            OpenApiParameter("search", str),
        ],
        responses={200: StudentTuitionAccountSerializer(many=True)},
        tags=["Finance"],
    )
    def get(self, request):
        queryset = StudentTuitionAccount.objects.filter(
            school=request.school,
        ).select_related(
            "plan",
            "enrollment__student",
            "enrollment__academic_year",
            "enrollment__classroom",
        ).prefetch_related(
            "plan__installments",
            "payments",
        )

        year = request.query_params.get("academic_year")
        classroom = request.query_params.get("classroom")
        search = request.query_params.get("search", "").strip()
        payment_status = request.query_params.get(
            "payment_status"
        )

        if year:
            queryset = queryset.filter(
                enrollment__academic_year_id=year,
            )
        if classroom:
            queryset = queryset.filter(
                enrollment__classroom_id=classroom,
            )
        if search:
            queryset = queryset.filter(
                Q(
                    enrollment__student__first_name__icontains=search
                )
                | Q(
                    enrollment__student__last_name__icontains=search
                )
                | Q(
                    enrollment__student__matricule__icontains=search
                )
            )

        items = []
        for account in queryset:
            enrich_account(account)
            if (
                payment_status
                and account.payment_status != payment_status
            ):
                continue
            items.append(account)

        return Response(
            StudentTuitionAccountSerializer(
                items,
                many=True,
            ).data
        )


class TuitionAccountDetailView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Détail du compte pension d'un élève",
        responses={200: StudentTuitionAccountSerializer},
        tags=["Finance"],
    )
    def get(self, request, account_id):
        account = get_object_or_404(
            StudentTuitionAccount.objects.select_related(
                "plan",
                "enrollment__student",
                "enrollment__academic_year",
                "enrollment__classroom",
            ).prefetch_related(
                "plan__installments",
                "payments",
            ),
            school=request.school,
            id=account_id,
        )
        enrich_account(account)

        return Response(
            StudentTuitionAccountSerializer(account).data
        )


class PaymentListView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Historique des paiements de pension",
        parameters=[
            OpenApiParameter("academic_year", int),
            OpenApiParameter("classroom", int),
            OpenApiParameter("student", int),
            OpenApiParameter("search", str),
        ],
        responses={200: TuitionPaymentSerializer(many=True)},
        tags=["Finance"],
    )
    def get(self, request):
        queryset = TuitionPayment.objects.filter(
            school=request.school,
        ).select_related(
            "received_by",
            "tuition_account__enrollment__student",
            "tuition_account__enrollment__classroom",
            "tuition_account__enrollment__academic_year",
        ).prefetch_related(
            "allocations__installment",
        )

        year = request.query_params.get("academic_year")
        classroom = request.query_params.get("classroom")
        student = request.query_params.get("student")
        search = request.query_params.get("search", "").strip()

        if year:
            queryset = queryset.filter(
                tuition_account__enrollment__academic_year_id=year,
            )
        if classroom:
            queryset = queryset.filter(
                tuition_account__enrollment__classroom_id=classroom,
            )
        if student:
            queryset = queryset.filter(
                tuition_account__enrollment__student_id=student,
            )
        if search:
            queryset = queryset.filter(
                Q(receipt_number__icontains=search)
                | Q(reference__icontains=search)
                | Q(
                    tuition_account__enrollment__student__first_name__icontains=search
                )
                | Q(
                    tuition_account__enrollment__student__last_name__icontains=search
                )
                | Q(
                    tuition_account__enrollment__student__matricule__icontains=search
                )
            )

        return Response(
            TuitionPaymentSerializer(
                queryset,
                many=True,
                context={"request": request},
            ).data
        )


class RecordPaymentView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Enregistrer un paiement de pension",
        description=(
            "Le paiement est automatiquement imputé aux tranches les plus "
            "anciennes non soldées et un reçu PDF immuable est généré."
        ),
        request=RecordPaymentSerializer,
        responses={201: RecordPaymentResultSerializer},
        tags=["Finance"],
    )
    def post(self, request):
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payment, account = record_payment(
                school=request.school,
                account_id=data["tuition_account"],
                amount=data["amount"],
                method=data["method"],
                reference=data.get("reference", ""),
                notes=data.get("notes", ""),
                paid_at=data.get("paid_at"),
                received_by=request.user,
            )
        except StudentTuitionAccount.DoesNotExist:
            return Response(
                {"detail": "Compte pension introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        payment = TuitionPayment.objects.select_related(
            "received_by",
            "tuition_account__enrollment__student",
            "tuition_account__enrollment__classroom",
            "tuition_account__enrollment__academic_year",
        ).prefetch_related(
            "allocations__installment",
        ).get(id=payment.id)

        return Response(
            {
                "payment": TuitionPaymentSerializer(
                    payment,
                    context={"request": request},
                ).data,
                "account": StudentTuitionAccountSerializer(
                    account,
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentReceiptView(APIView):
    permission_classes = [IsAuthenticated, CanUseFinance]

    @extend_schema(
        summary="Télécharger le reçu PDF d'un paiement",
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
        tags=["Finance"],
    )
    def get(self, request, payment_id):
        payment = get_object_or_404(
            TuitionPayment.objects.select_related("receipt"),
            school=request.school,
            id=payment_id,
        )

        if not hasattr(payment, "receipt"):
            return Response(
                {"detail": "Aucun reçu n'est disponible pour ce paiement."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            payment.receipt.pdf_file.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"{payment.receipt_number}.pdf",
        )
