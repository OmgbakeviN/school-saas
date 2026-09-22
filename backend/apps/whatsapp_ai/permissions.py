import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasWhatsAppAgentKey(BasePermission):
    message = "Clé interne WhatsApp/IA invalide."

    def has_permission(self, request, view):
        expected = str(
            getattr(settings, "WHATSAPP_AGENT_API_KEY", "") or ""
        )
        provided = str(
            request.headers.get("X-Bewise-Agent-Key", "") or ""
        )
        if not expected or not provided:
            return False
        return secrets.compare_digest(expected, provided)
