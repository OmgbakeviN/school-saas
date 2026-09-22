import base64
import json
from urllib import error, request

from django.conf import settings

from .phone import provider_phone


class EvolutionAPIError(RuntimeError):
    pass


class WhatsAppProvider:
    def send_text(self, *, connection, number, text):
        raise NotImplementedError

    def send_document(
        self,
        *,
        connection,
        number,
        pdf_bytes,
        filename,
        caption="",
    ):
        raise NotImplementedError


class EvolutionWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        self.base_url = str(
            getattr(settings, "EVOLUTION_API_URL", "") or ""
        ).rstrip("/")
        self.api_key = str(
            getattr(settings, "EVOLUTION_API_KEY", "") or ""
        )
        self.timeout = int(
            getattr(settings, "EVOLUTION_API_TIMEOUT", 30)
        )
        self.dry_run = bool(
            getattr(settings, "WHATSAPP_AI_DRY_RUN", False)
        )

    def _post(self, path, payload):
        if self.dry_run:
            return {
                "dry_run": True,
                "status": "SIMULATED",
                "payload": {
                    key: value
                    for key, value in payload.items()
                    if key != "media"
                },
            }

        if not self.base_url or not self.api_key:
            raise EvolutionAPIError(
                "EVOLUTION_API_URL / EVOLUTION_API_KEY non configurés."
            )

        url = f"{self.base_url}/{path.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "apikey": self.api_key,
            },
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise EvolutionAPIError(
                f"Evolution API HTTP {exc.code}: {detail[:800]}"
            ) from exc
        except error.URLError as exc:
            raise EvolutionAPIError(
                f"Evolution API inaccessible: {exc.reason}"
            ) from exc

    def send_text(self, *, connection, number, text):
        return self._post(
            f"message/sendText/{connection.instance_name}",
            {
                "number": provider_phone(number),
                "text": str(text or ""),
                "delay": 500,
                "linkPreview": False,
            },
        )

    def send_document(
        self,
        *,
        connection,
        number,
        pdf_bytes,
        filename,
        caption="",
    ):
        encoded = base64.b64encode(pdf_bytes).decode("ascii")
        return self._post(
            f"message/sendMedia/{connection.instance_name}",
            {
                "number": provider_phone(number),
                "mediatype": "document",
                "mimetype": "application/pdf",
                "caption": str(caption or ""),
                "media": encoded,
                "fileName": filename,
                "delay": 700,
                "linkPreview": False,
            },
        )


def get_provider(connection):
    if connection.provider == connection.Provider.EVOLUTION:
        return EvolutionWhatsAppProvider()
    raise EvolutionAPIError(
        f"Provider WhatsApp non supporté: {connection.provider}"
    )


def provider_message_id(response):
    if not isinstance(response, dict):
        return ""
    key = response.get("key") or {}
    if isinstance(key, dict):
        return str(key.get("id") or "")
    return ""
