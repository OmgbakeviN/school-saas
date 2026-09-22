from django.urls import path

from .views import (
    AgentContextView,
    AgentHealthView,
    PreviewTuitionInvoiceView,
    SendAgentTextView,
    SendTermReportCardToolView,
    SendTuitionInvoiceToolView,
)


urlpatterns = [
    path("health/", AgentHealthView.as_view(), name="whatsapp-ai-health"),
    path("context/", AgentContextView.as_view(), name="whatsapp-ai-context"),
    path(
        "tools/send-term-report-card/",
        SendTermReportCardToolView.as_view(),
        name="whatsapp-ai-send-term-report-card",
    ),
    path(
        "tools/preview-tuition-invoice/",
        PreviewTuitionInvoiceView.as_view(),
        name="whatsapp-ai-preview-tuition-invoice",
    ),
    path(
        "tools/send-tuition-invoice/",
        SendTuitionInvoiceToolView.as_view(),
        name="whatsapp-ai-send-tuition-invoice",
    ),
    path("send-text/", SendAgentTextView.as_view(), name="whatsapp-ai-send-text"),
]
