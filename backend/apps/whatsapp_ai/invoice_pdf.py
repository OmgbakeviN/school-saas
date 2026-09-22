from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


LABELS = {
    "FR": {
        "title": "FACTURE / ÉTAT DE PENSION",
        "invoice": "Facture",
        "issued": "Émise le",
        "student": "Élève",
        "matricule": "Matricule",
        "classroom": "Classe",
        "year": "Année scolaire",
        "plan": "Plan de pension",
        "installment": "Tranche",
        "amount": "Montant",
        "paid": "Payé",
        "remaining": "Reste",
        "due": "Échéance",
        "status": "Statut",
        "paid_status": "Soldée",
        "open_status": "À payer",
        "expected": "Pension annuelle",
        "paid_total": "Total payé",
        "balance": "Reste à payer",
        "note": (
            "Ce document présente la situation actuelle de la pension. "
            "Les reçus de paiement restent les justificatifs d'encaissement."
        ),
    },
    "EN": {
        "title": "TUITION INVOICE / STATEMENT",
        "invoice": "Invoice",
        "issued": "Issued on",
        "student": "Student",
        "matricule": "Student ID",
        "classroom": "Class",
        "year": "Academic year",
        "plan": "Tuition plan",
        "installment": "Installment",
        "amount": "Amount",
        "paid": "Paid",
        "remaining": "Balance",
        "due": "Due date",
        "status": "Status",
        "paid_status": "Paid",
        "open_status": "Due",
        "expected": "Annual tuition",
        "paid_total": "Total paid",
        "balance": "Outstanding",
        "note": (
            "This document shows the current tuition position. Payment "
            "receipts remain the official proof of collection."
        ),
    },
}


def _color(value, fallback):
    try:
        return colors.HexColor(value or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _money(value):
    try:
        amount = float(value)
    except Exception:
        return str(value or "0")
    return f"{amount:,.0f}".replace(",", " ")


def generate_tuition_invoice_pdf(*, payload, logo_path=None):
    language = payload.get("language") or "FR"
    labels = LABELS.get(language, LABELS["FR"])

    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{labels['title']} - {payload['student']['name']}",
        author=payload["school"]["name"],
    )

    primary = _color(payload["school"].get("primary_color"), "#0f172a")
    secondary = _color(payload["school"].get("secondary_color"), "#2563eb")

    styles = getSampleStyleSheet()
    school_style = ParagraphStyle(
        "School",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        alignment=TA_CENTER,
        textColor=primary,
    )
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=20,
        alignment=TA_CENTER,
        textColor=secondary,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )
    small = ParagraphStyle(
        "Small",
        parent=body,
        fontSize=7.4,
        leading=9.2,
        textColor=colors.HexColor("#64748b"),
    )
    right = ParagraphStyle("Right", parent=body, alignment=TA_RIGHT)

    story = []
    logo = None
    if logo_path:
        try:
            logo = Image(logo_path, width=22 * mm, height=22 * mm)
        except Exception:
            logo = None

    school_lines = [
        Paragraph(payload["school"]["name"], school_style),
        Paragraph(payload["school"].get("motto") or "", small),
        Paragraph(
            " • ".join(
                item
                for item in [
                    payload["school"].get("city"),
                    payload["school"].get("phone"),
                    payload["school"].get("email"),
                ]
                if item
            ),
            small,
        ),
    ]

    if logo:
        header = Table([[logo, school_lines]], colWidths=[28 * mm, 151 * mm])
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ]))
        story.append(header)
    else:
        story.extend(school_lines)

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(labels["title"], title_style))
    story.append(
        Paragraph(
            f"{labels['invoice']} N° {payload['invoice_number']} • "
            f"{labels['issued']} {payload['issued_at_display']}",
            small,
        )
    )
    story.append(Spacer(1, 5 * mm))

    info = Table(
        [
            [labels["student"], payload["student"]["name"], labels["matricule"], payload["student"]["matricule"]],
            [labels["classroom"], payload["academic"]["classroom"], labels["year"], payload["academic"]["academic_year"]],
            [labels["plan"], payload["plan"]["name"], "", ""],
        ],
        colWidths=[28 * mm, 62 * mm, 29 * mm, 60 * mm],
    )
    info.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fafc")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("SPAN", (1, 2), (3, 2)),
    ]))
    story.append(info)
    story.append(Spacer(1, 5 * mm))

    currency = payload["plan"]["currency"]
    rows = [[
        labels["installment"],
        labels["amount"],
        labels["paid"],
        labels["remaining"],
        labels["due"],
        labels["status"],
    ]]
    for item in payload["installments"]:
        rows.append([
            item["name"],
            f"{_money(item['amount'])} {currency}",
            f"{_money(item['paid'])} {currency}",
            f"{_money(item['remaining'])} {currency}",
            item.get("due_date_display") or "-",
            labels["paid_status"] if item["is_paid"] else labels["open_status"],
        ])

    installments = Table(
        rows,
        colWidths=[43 * mm, 30 * mm, 28 * mm, 29 * mm, 27 * mm, 22 * mm],
        repeatRows=1,
    )
    installments.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("FONTSIZE", (0, 0), (-1, -1), 7.1),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (3, -1), "RIGHT"),
        ("ALIGN", (4, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(installments)
    story.append(Spacer(1, 5 * mm))

    totals = payload["totals"]
    summary = Table(
        [
            [labels["expected"], f"{_money(totals['expected'])} {currency}"],
            [labels["paid_total"], f"{_money(totals['paid'])} {currency}"],
            [labels["balance"], f"{_money(totals['balance'])} {currency}"],
        ],
        colWidths=[90 * mm, 89 * mm],
    )
    summary.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#eff6ff")),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(labels["note"], small))

    doc.build(story)
    return output.getvalue()
