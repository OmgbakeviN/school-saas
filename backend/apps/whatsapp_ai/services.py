import re
import unicodedata
from decimal import Decimal

from django.utils import timezone

from apps.finance.models import StudentTuitionAccount
from apps.finance.services import account_summary, json_safe
from apps.people.models import Enrollment, StudentGuardian
from apps.report_cards.models import ReportCardSnapshot

from .invoice_pdf import generate_tuition_invoice_pdf
from .models import (
    GuardianWhatsAppIdentity,
    StudentGuardianDocumentPermission,
    WhatsAppConnection,
    WhatsAppMessageLog,
)
from .phone import normalize_phone
from .provider import get_provider, provider_message_id


class AgentAccessError(RuntimeError):
    pass


class AgentDocumentError(RuntimeError):
    pass


def _plain(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value).strip().lower()


def _student_name(student):
    return f"{student.last_name} {student.first_name}".strip()


def _provider_response_metadata(response):
    if not isinstance(response, dict):
        return {}
    if response.get("dry_run"):
        return {"dry_run": True, "status": response.get("status")}
    return {
        "status": response.get("status"),
        "message_id": provider_message_id(response),
    }


def get_connection(instance_name):
    try:
        return WhatsAppConnection.objects.select_related("school").get(
            instance_name=str(instance_name or "").strip(),
            is_active=True,
        )
    except WhatsAppConnection.DoesNotExist as exc:
        raise AgentAccessError(
            "Cette instance WhatsApp n'est pas reliée à un établissement actif."
        ) from exc


def resolve_identity(*, connection, phone):
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    return (
        GuardianWhatsAppIdentity.objects
        .select_related("guardian", "school")
        .filter(
            school=connection.school,
            normalized_phone=normalized,
            phone_verified=True,
            whatsapp_enabled=True,
            guardian__is_active=True,
        )
        .first()
    )


def _link_permission(link):
    try:
        return link.whatsapp_document_permission
    except StudentGuardianDocumentPermission.DoesNotExist:
        return None


def _current_enrollment(student, school):
    enrollment = (
        Enrollment.objects.filter(
            school=school,
            student=student,
            status=Enrollment.Status.ACTIVE,
        )
        .select_related(
            "academic_year",
            "classroom__level__cycle__section",
        )
        .order_by("-academic_year__start_date", "-id")
        .first()
    )
    if enrollment:
        return enrollment

    return (
        Enrollment.objects.filter(school=school, student=student)
        .select_related(
            "academic_year",
            "classroom__level__cycle__section",
        )
        .order_by("-academic_year__start_date", "-id")
        .first()
    )


def _latest_period_snapshots(enrollment):
    snapshots = (
        ReportCardSnapshot.objects.filter(
            school=enrollment.school,
            enrollment=enrollment,
            academic_year=enrollment.academic_year,
            report_type=ReportCardSnapshot.ReportType.PERIOD,
        )
        .select_related("academic_period")
        .order_by("academic_period__order", "-version", "-published_at")
    )

    by_period = {}
    for snapshot in snapshots:
        if snapshot.academic_period_id not in by_period:
            by_period[snapshot.academic_period_id] = snapshot

    return sorted(
        by_period.values(),
        key=lambda item: (
            item.academic_period.order,
            item.academic_period.name.lower(),
        ),
    )


def build_parent_context(*, connection, phone):
    identity = resolve_identity(connection=connection, phone=phone)
    normalized = normalize_phone(phone)

    if identity is None:
        return {
            "authorized": False,
            "phone": normalized,
            "reason": "UNKNOWN_OR_UNVERIFIED_PHONE",
            "safe_message_fr": (
                "Ce numéro WhatsApp n'est pas autorisé à accéder aux documents "
                "des élèves. Veuillez contacter l'administration de l'établissement."
            ),
            "safe_message_en": (
                "This WhatsApp number is not authorized to access student documents. "
                "Please contact the school administration."
            ),
        }

    guardian = identity.guardian
    children = []

    links = (
        StudentGuardian.objects.filter(
            school=connection.school,
            guardian=guardian,
        )
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    for link in links:
        permission = _link_permission(link)
        enrollment = _current_enrollment(link.student, connection.school)
        if enrollment is None:
            continue

        can_report = bool(
            link.can_receive_results
            and (permission is None or permission.can_receive_report_cards)
        )
        can_finance = bool(
            permission is not None and permission.can_receive_finance
        )

        reports = []
        if can_report:
            for snapshot in _latest_period_snapshots(enrollment):
                payload_language = (
                    snapshot.payload.get("language", {})
                    if isinstance(snapshot.payload, dict)
                    else {}
                )
                reports.append({
                    "period_id": snapshot.academic_period_id,
                    "period_name": snapshot.academic_period.name,
                    "period_order": snapshot.academic_period.order,
                    "period_kind": snapshot.academic_period.kind,
                    "version": snapshot.version,
                    "language": (
                        payload_language.get("code")
                        if isinstance(payload_language, dict)
                        else None
                    ),
                })

        has_finance = (
            can_finance
            and StudentTuitionAccount.objects.filter(
                school=connection.school,
                enrollment=enrollment,
            ).exists()
        )

        children.append({
            "student_id": link.student_id,
            "name": _student_name(link.student),
            "matricule": link.student.matricule,
            "classroom": enrollment.classroom.name,
            "level": enrollment.classroom.level.name,
            "academic_year": enrollment.academic_year.name,
            "permissions": {
                "report_cards": can_report,
                "finance": can_finance,
            },
            "available_report_cards": reports,
            "tuition_invoice_available": has_finance,
        })

    return {
        "authorized": True,
        "school": {
            "id": connection.school_id,
            "name": connection.school.name,
            "slug": connection.school.slug,
        },
        "guardian": {
            "id": guardian.id,
            "name": f"{guardian.last_name} {guardian.first_name}".strip(),
            "preferred_language": guardian.preferred_language,
        },
        "phone": normalized,
        "session_key": f"{connection.instance_name}:{normalized}",
        "children": children,
        "capabilities": [
            "SEND_PERIOD_REPORT_CARD",
            "SEND_TUITION_INVOICE",
        ],
    }


def require_parent_context(*, connection, phone):
    context = build_parent_context(connection=connection, phone=phone)
    if not context.get("authorized"):
        raise AgentAccessError(
            "Ce numéro n'est pas autorisé pour cet établissement."
        )
    return context


def _authorized_link(*, connection, identity, student_id):
    try:
        link = (
            StudentGuardian.objects.select_related("student", "guardian")
            .get(
                school=connection.school,
                guardian=identity.guardian,
                student_id=student_id,
            )
        )
    except StudentGuardian.DoesNotExist as exc:
        raise AgentAccessError(
            "Cet élève n'est pas lié au parent WhatsApp autorisé."
        ) from exc
    return link


def _period_target(selector):
    text = _plain(selector)
    if not text or text in {"latest", "dernier", "derniere", "recent", "current"}:
        return None

    match = re.search(r"\b([1-9])\b", text)
    if match:
        return int(match.group(1))

    aliases = {
        1: ("premier", "1er", "first", "one"),
        2: ("deuxieme", "second", "2e", "2eme", "two"),
        3: ("troisieme", "third", "3e", "3eme", "three"),
        4: ("quatrieme", "fourth", "4e", "4eme", "four"),
    }
    for order, values in aliases.items():
        if any(value in text for value in values):
            return order
    return text


def _select_period_snapshot(enrollment, selector):
    snapshots = _latest_period_snapshots(enrollment)
    if not snapshots:
        raise AgentDocumentError(
            "Aucun bulletin de période publié n'est disponible pour cet élève."
        )

    target = _period_target(selector)
    if target is None:
        return snapshots[-1]

    if isinstance(target, int):
        for snapshot in snapshots:
            if snapshot.academic_period.order == target:
                return snapshot
    else:
        for snapshot in snapshots:
            period = snapshot.academic_period
            if target in _plain(period.name) or target == _plain(period.code):
                return snapshot

    available = ", ".join(item.academic_period.name for item in snapshots)
    raise AgentDocumentError(
        f"Ce bulletin n'est pas disponible. Périodes disponibles : {available}."
    )


def _caption_language(identity):
    return "EN" if identity.guardian.preferred_language == "EN" else "FR"


def _read_snapshot_pdf(snapshot):
    if not snapshot.pdf_file:
        raise AgentDocumentError("Le fichier PDF du bulletin est introuvable.")
    try:
        snapshot.pdf_file.open("rb")
        return snapshot.pdf_file.read()
    except Exception as exc:
        raise AgentDocumentError(
            "Le fichier PDF du bulletin ne peut pas être lu."
        ) from exc
    finally:
        try:
            snapshot.pdf_file.close()
        except Exception:
            pass


def send_period_report_card(
    *,
    connection,
    phone,
    student_id,
    period=None,
):
    identity = resolve_identity(connection=connection, phone=phone)
    if identity is None:
        raise AgentAccessError("Parent WhatsApp non autorisé.")

    link = _authorized_link(
        connection=connection,
        identity=identity,
        student_id=student_id,
    )
    permission = _link_permission(link)

    if not link.can_receive_results:
        raise AgentAccessError(
            "Ce parent n'est pas autorisé à recevoir les résultats de cet élève."
        )
    if permission is not None and not permission.can_receive_report_cards:
        raise AgentAccessError(
            "L'envoi des bulletins WhatsApp est désactivé pour ce lien parent/élève."
        )

    enrollment = _current_enrollment(link.student, connection.school)
    if enrollment is None:
        raise AgentDocumentError("Aucune inscription scolaire trouvée pour cet élève.")

    snapshot = _select_period_snapshot(enrollment, period)
    pdf_bytes = _read_snapshot_pdf(snapshot)

    language = _caption_language(identity)
    name = _student_name(link.student)
    period_name = snapshot.academic_period.name
    if language == "EN":
        caption = f"Report card — {name} — {period_name}"
    else:
        caption = f"Bulletin — {name} — {period_name}"

    safe_period = re.sub(r"[^A-Za-z0-9_-]+", "-", _plain(period_name)).strip("-")
    filename = f"bulletin-{link.student.matricule}-{safe_period or snapshot.academic_period_id}.pdf"

    provider = get_provider(connection)
    response = provider.send_document(
        connection=connection,
        number=phone,
        pdf_bytes=pdf_bytes,
        filename=filename,
        caption=caption,
    )

    WhatsAppMessageLog.objects.create(
        school=connection.school,
        connection=connection,
        guardian=identity.guardian,
        direction=WhatsAppMessageLog.Direction.OUTBOUND,
        kind=WhatsAppMessageLog.Kind.DOCUMENT,
        phone=normalize_phone(phone),
        provider_message_id=provider_message_id(response),
        text=caption,
        metadata={
            "tool": "send_period_report_card",
            "student_id": link.student_id,
            "snapshot_id": snapshot.id,
            "period_id": snapshot.academic_period_id,
            "filename": filename,
            **_provider_response_metadata(response),
        },
    )

    return {
        "sent": True,
        "document_type": "PERIOD_REPORT_CARD",
        "student": name,
        "period": period_name,
        "academic_year": enrollment.academic_year.name,
        "version": snapshot.version,
        "filename": filename,
        "dry_run": bool(response.get("dry_run")) if isinstance(response, dict) else False,
    }


def _invoice_payload(*, account, language):
    enrollment = account.enrollment
    school = account.school
    summary = account_summary(account)
    today = timezone.localdate()

    installments = []
    for row in summary["installments"]:
        due_date = row.get("due_date")
        installments.append({
            "id": row["id"],
            "name": row["name"],
            "amount": row["amount"],
            "paid": row["paid"],
            "remaining": row["remaining"],
            "due_date": due_date,
            "due_date_display": due_date.strftime("%d/%m/%Y") if due_date else "",
            "is_paid": row["is_paid"],
        })

    payload = {
        "schema_version": 1,
        "language": language,
        "invoice_number": (
            f"TUI-{enrollment.academic_year.start_date.year}-{account.id:06d}"
        ),
        "issued_at": today,
        "issued_at_display": today.strftime("%d/%m/%Y"),
        "school": {
            "id": school.id,
            "name": school.name,
            "acronym": school.acronym,
            "motto": school.motto,
            "city": school.city,
            "country": school.country,
            "phone": school.phone,
            "email": school.email,
            "primary_color": school.primary_color,
            "secondary_color": school.secondary_color,
        },
        "student": {
            "id": enrollment.student_id,
            "name": _student_name(enrollment.student),
            "matricule": enrollment.student.matricule,
        },
        "academic": {
            "academic_year": enrollment.academic_year.name,
            "classroom": enrollment.classroom.name,
            "level": enrollment.classroom.level.name,
        },
        "plan": {
            "id": account.plan_id,
            "name": account.plan.name,
            "currency": account.plan.currency,
        },
        "installments": installments,
        "totals": {
            "expected": summary["expected_amount"],
            "paid": summary["paid_amount"],
            "balance": summary["balance"],
            "status": summary["payment_status"],
        },
    }
    return json_safe(payload)


def prepare_tuition_invoice(*, connection, phone, student_id):
    identity = resolve_identity(connection=connection, phone=phone)
    if identity is None:
        raise AgentAccessError("Parent WhatsApp non autorisé.")

    link = _authorized_link(
        connection=connection,
        identity=identity,
        student_id=student_id,
    )
    permission = _link_permission(link)
    if permission is None or not permission.can_receive_finance:
        raise AgentAccessError(
            "Ce parent n'est pas autorisé à recevoir les documents de pension de cet élève."
        )

    enrollment = _current_enrollment(link.student, connection.school)
    if enrollment is None:
        raise AgentDocumentError("Aucune inscription scolaire trouvée pour cet élève.")

    try:
        account = (
            StudentTuitionAccount.objects.select_related(
                "school",
                "plan",
                "enrollment__student",
                "enrollment__academic_year",
                "enrollment__classroom__level",
            )
            .prefetch_related("plan__installments", "payments")
            .get(
                school=connection.school,
                enrollment=enrollment,
            )
        )
    except StudentTuitionAccount.DoesNotExist as exc:
        raise AgentDocumentError(
            "Aucun compte de pension n'est configuré pour cet élève."
        ) from exc

    language = _caption_language(identity)
    payload = _invoice_payload(account=account, language=language)

    logo_path = None
    try:
        if connection.school.logo:
            logo_path = connection.school.logo.path
    except Exception:
        logo_path = None

    pdf_bytes = generate_tuition_invoice_pdf(
        payload=payload,
        logo_path=logo_path,
    )

    student_name = payload["student"]["name"]
    invoice_number = payload["invoice_number"]
    if language == "EN":
        caption = f"Tuition invoice — {student_name} — {payload['academic']['academic_year']}"
    else:
        caption = f"Facture de pension — {student_name} — {payload['academic']['academic_year']}"

    filename = f"facture-pension-{link.student.matricule}-{invoice_number}.pdf"
    return {
        "identity": identity,
        "link": link,
        "account": account,
        "payload": payload,
        "pdf_bytes": pdf_bytes,
        "caption": caption,
        "filename": filename,
    }


def send_tuition_invoice(*, connection, phone, student_id):
    document = prepare_tuition_invoice(
        connection=connection,
        phone=phone,
        student_id=student_id,
    )
    identity = document["identity"]
    link = document["link"]
    account = document["account"]
    payload = document["payload"]
    filename = document["filename"]
    caption = document["caption"]

    provider = get_provider(connection)
    response = provider.send_document(
        connection=connection,
        number=phone,
        pdf_bytes=document["pdf_bytes"],
        filename=filename,
        caption=caption,
    )

    WhatsAppMessageLog.objects.create(
        school=connection.school,
        connection=connection,
        guardian=identity.guardian,
        direction=WhatsAppMessageLog.Direction.OUTBOUND,
        kind=WhatsAppMessageLog.Kind.DOCUMENT,
        phone=normalize_phone(phone),
        provider_message_id=provider_message_id(response),
        text=caption,
        metadata={
            "tool": "send_tuition_invoice",
            "student_id": link.student_id,
            "tuition_account_id": account.id,
            "invoice_number": payload["invoice_number"],
            "filename": filename,
            **_provider_response_metadata(response),
        },
    )

    return {
        "sent": True,
        "document_type": "TUITION_INVOICE",
        "student": payload["student"]["name"],
        "academic_year": payload["academic"]["academic_year"],
        "invoice_number": payload["invoice_number"],
        "filename": filename,
        "dry_run": bool(response.get("dry_run")) if isinstance(response, dict) else False,
    }

def send_agent_text(*, connection, phone, text):
    provider = get_provider(connection)
    response = provider.send_text(
        connection=connection,
        number=phone,
        text=text,
    )

    identity = resolve_identity(connection=connection, phone=phone)
    WhatsAppMessageLog.objects.create(
        school=connection.school,
        connection=connection,
        guardian=identity.guardian if identity else None,
        direction=WhatsAppMessageLog.Direction.OUTBOUND,
        kind=WhatsAppMessageLog.Kind.TEXT,
        phone=normalize_phone(phone),
        provider_message_id=provider_message_id(response),
        text=text,
        metadata={
            "source": "n8n_agent",
            **_provider_response_metadata(response),
        },
    )
    return {
        "sent": True,
        "dry_run": bool(response.get("dry_run")) if isinstance(response, dict) else False,
    }
