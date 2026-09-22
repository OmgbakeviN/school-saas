from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WhatsAppConnection, WhatsAppMessageLog
from .permissions import HasWhatsAppAgentKey
from .provider import EvolutionAPIError
from .serializers import (
    AgentContextRequestSerializer,
    SendAgentTextSerializer,
    SendTermReportCardSerializer,
    SendTuitionInvoiceSerializer,
)
from .phone import normalize_phone
from .services import (
    AgentAccessError,
    AgentDocumentError,
    build_parent_context,
    get_connection,
    prepare_tuition_invoice,
    send_agent_text,
    send_period_report_card,
    send_tuition_invoice,
)


class AgentHealthView(APIView):
    permission_classes = [HasWhatsAppAgentKey]
    authentication_classes = []

    @extend_schema(
        summary="Santé de l'intégration WhatsApp IA",
        responses={200: OpenApiTypes.OBJECT},
        tags=["WhatsApp AI"],
    )
    def get(self, request):
        return Response({
            "status": "ok",
            "connections": WhatsAppConnection.objects.filter(
                is_active=True
            ).count(),
            "dry_run": bool(
                getattr(settings, "WHATSAPP_AI_DRY_RUN", False)
            ),
            "evolution_configured": bool(
                getattr(settings, "EVOLUTION_API_URL", "")
                and getattr(settings, "EVOLUTION_API_KEY", "")
            ),
        })


class AgentContextView(APIView):
    permission_classes = [HasWhatsAppAgentKey]
    authentication_classes = []

    @extend_schema(
        summary="Résoudre le parent WhatsApp et ses enfants autorisés",
        request=AgentContextRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["WhatsApp AI"],
    )
    def post(self, request):
        serializer = AgentContextRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            connection = get_connection(data["instance_name"])
        except AgentAccessError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        context = build_parent_context(
            connection=connection,
            phone=data["phone"],
        )

        if data.get("message_text"):
            guardian_id = (context.get("guardian") or {}).get("id")
            WhatsAppMessageLog.objects.create(
                school=connection.school,
                connection=connection,
                guardian_id=guardian_id,
                direction=WhatsAppMessageLog.Direction.INBOUND,
                kind=WhatsAppMessageLog.Kind.TEXT,
                phone=normalize_phone(data["phone"]),
                text=data["message_text"],
                metadata={"source": "evolution_webhook_via_n8n"},
            )

        return Response(context)


class SendTermReportCardToolView(APIView):
    permission_classes = [HasWhatsAppAgentKey]
    authentication_classes = []

    @extend_schema(
        summary="Outil IA — envoyer un bulletin de période publié",
        request=SendTermReportCardSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["WhatsApp AI"],
    )
    def post(self, request):
        serializer = SendTermReportCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            connection = get_connection(data["instance_name"])
            result = send_period_report_card(
                connection=connection,
                phone=data["phone"],
                student_id=data["student_id"],
                period=data.get("period"),
            )
            return Response(result)
        except AgentAccessError as exc:
            return Response(
                {"sent": False, "detail": str(exc), "error": "FORBIDDEN"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except AgentDocumentError as exc:
            return Response(
                {"sent": False, "detail": str(exc), "error": "NOT_AVAILABLE"},
                status=status.HTTP_409_CONFLICT,
            )
        except EvolutionAPIError as exc:
            return Response(
                {"sent": False, "detail": str(exc), "error": "PROVIDER_ERROR"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class PreviewTuitionInvoiceView(APIView):
    permission_classes = [HasWhatsAppAgentKey]
    authentication_classes = []

    @extend_schema(
        summary="Prévisualiser la facture de pension PDF sans l'envoyer",
        request=SendTuitionInvoiceSerializer,
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
        tags=["WhatsApp AI"],
    )
    def post(self, request):
        serializer = SendTuitionInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            connection = get_connection(data["instance_name"])
            document = prepare_tuition_invoice(
                connection=connection,
                phone=data["phone"],
                student_id=data["student_id"],
            )
        except AgentAccessError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except AgentDocumentError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        response = HttpResponse(
            document["pdf_bytes"],
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            f'inline; filename="{document["filename"]}"'
        )
        return response


class SendTuitionInvoiceToolView(APIView):
    permission_classes = [HasWhatsAppAgentKey]
    authentication_classes = []

    @extend_schema(
        summary="Outil IA — envoyer la facture / situation de pension PDF",
        request=SendTuitionInvoiceSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["WhatsApp AI"],
    )
    def post(self, request):
        serializer = SendTuitionInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            connection = get_connection(data["instance_name"])
            result = send_tuition_invoice(
                connection=connection,
                phone=data["phone"],
                student_id=data["student_id"],
            )
            return Response(result)
        except AgentAccessError as exc:
            return Response(
                {"sent": False, "detail": str(exc), "error": "FORBIDDEN"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except AgentDocumentError as exc:
            return Response(
                {"sent": False, "detail": str(exc), "error": "NOT_AVAILABLE"},
                status=status.HTTP_409_CONFLICT,
            )
        except EvolutionAPIError as exc:
            return Response(
                {"sent": False, "detail": str(exc), "error": "PROVIDER_ERROR"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class SendAgentTextView(APIView):
    permission_classes = [HasWhatsAppAgentKey]
    authentication_classes = []

    @extend_schema(
        summary="Envoyer la réponse texte finale de l'agent n8n",
        request=SendAgentTextSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["WhatsApp AI"],
    )
    def post(self, request):
        serializer = SendAgentTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            connection = get_connection(data["instance_name"])
            return Response(
                send_agent_text(
                    connection=connection,
                    phone=data["phone"],
                    text=data["text"],
                )
            )
        except AgentAccessError as exc:
            return Response(
                {"sent": False, "detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except EvolutionAPIError as exc:
            return Response(
                {"sent": False, "detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
