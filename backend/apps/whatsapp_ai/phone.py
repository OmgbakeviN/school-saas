import re

from django.conf import settings


def normalize_phone(value, *, default_country_code=None):
    """Return an E.164-like value (+2376...) suitable for identity lookup."""
    raw = str(value or "").strip()
    if not raw:
        return ""

    # Evolution commonly gives 2376...@s.whatsapp.net.
    raw = raw.split("@", 1)[0]
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""

    if digits.startswith("00"):
        digits = digits[2:]

    country_code = str(
        default_country_code
        or getattr(settings, "WHATSAPP_DEFAULT_COUNTRY_CODE", "237")
        or "237"
    ).lstrip("+")

    # Cameroon local mobile numbers are normally 9 digits.
    if len(digits) == 9 and not digits.startswith(country_code):
        digits = f"{country_code}{digits}"

    return f"+{digits}"


def provider_phone(value):
    """Evolution expects the international number without the leading +."""
    return normalize_phone(value).lstrip("+")
