from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A5
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


def generate_payment_receipt_pdf(*, payload, logo_path=None):
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A5,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=9 * mm,
        bottomMargin=9 * mm,
        title=f"Reçu {payload['receipt_number']}",
        author=payload["school"]["name"],
    )

    primary = _color(
        payload["school"].get("primary_color"),
        "#0f172a",
    )
    secondary = _color(
        payload["school"].get("secondary_color"),
        "#2563eb",
    )

    styles = getSampleStyleSheet()
    school_style = ParagraphStyle(
        "School",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=primary,
    )
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
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
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#64748b"),
    )
    right = ParagraphStyle(
        "Right",
        parent=body,
        alignment=TA_RIGHT,
    )

    story = []

    logo = None
    if logo_path:
        try:
            logo = Image(logo_path, width=18 * mm, height=18 * mm)
        except Exception:
            logo = None

    school_lines = [
        Paragraph(payload["school"]["name"], school_style),
        Paragraph(
            payload["school"].get("motto") or "",
            small,
        ),
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
        header = Table(
            [[logo, school_lines]],
            colWidths=[22 * mm, 105 * mm],
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ]))
        story.append(header)
    else:
        story.extend(school_lines)

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("REÇU DE PAIEMENT DE PENSION", title_style))
    story.append(
        Paragraph(
            f"N° {payload['receipt_number']} • {payload['paid_at_display']}",
            small,
        )
    )
    story.append(Spacer(1, 4 * mm))

    info = Table(
        [
            [
                Paragraph("<b>Élève</b>", body),
                Paragraph(payload["student"]["name"], body),
            ],
            [
                Paragraph("<b>Matricule</b>", body),
                Paragraph(payload["student"]["matricule"], body),
            ],
            [
                Paragraph("<b>Classe</b>", body),
                Paragraph(payload["academic"]["classroom"], body),
            ],
            [
                Paragraph("<b>Année scolaire</b>", body),
                Paragraph(payload["academic"]["academic_year"], body),
            ],
            [
                Paragraph("<b>Plan de pension</b>", body),
                Paragraph(payload["plan"]["name"], body),
            ],
        ],
        colWidths=[39 * mm, 88 * mm],
    )
    info.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(info)
    story.append(Spacer(1, 4 * mm))

    payment = Table(
        [
            [
                Paragraph("<b>Montant versé</b>", body),
                Paragraph(
                    f"<b>{_money(payload['payment']['amount'])} "
                    f"{payload['plan']['currency']}</b>",
                    right,
                ),
            ],
            [
                Paragraph("<b>Mode de paiement</b>", body),
                Paragraph(payload["payment"]["method_label"], right),
            ],
            [
                Paragraph("<b>Référence</b>", body),
                Paragraph(payload["payment"].get("reference") or "-", right),
            ],
        ],
        colWidths=[58 * mm, 69 * mm],
    )
    payment.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 0.8, secondary),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bfdbfe")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(payment)
    story.append(Spacer(1, 4 * mm))

    allocations = [["Tranche", "Montant imputé"]]
    for allocation in payload.get("allocations", []):
        allocations.append([
            allocation["name"],
            f"{_money(allocation['amount'])} {payload['plan']['currency']}",
        ])

    alloc_table = Table(
        allocations,
        colWidths=[76 * mm, 51 * mm],
        repeatRows=1,
    )
    alloc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(alloc_table)
    story.append(Spacer(1, 4 * mm))

    balance = payload["balance"]
    balance_table = Table(
        [
            ["Pension totale", f"{_money(balance['expected'])} {payload['plan']['currency']}"],
            ["Total payé", f"{_money(balance['paid_after'])} {payload['plan']['currency']}"],
            ["Reste à payer", f"{_money(balance['remaining_after'])} {payload['plan']['currency']}"],
        ],
        colWidths=[63 * mm, 64 * mm],
    )
    balance_table.setStyle(TableStyle([
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(balance_table)
    story.append(Spacer(1, 7 * mm))

    footer = Table(
        [[
            Paragraph(
                "<b>Encaissement effectué par</b><br/><br/>"
                + payload["received_by"],
                small,
            ),
            Paragraph(
                "Cachet / signature<br/><br/><br/>",
                small,
            ),
        ]],
        colWidths=[64 * mm, 63 * mm],
    )
    footer.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(footer)
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            f"Empreinte du reçu : {payload['fingerprint']}",
            small,
        )
    )

    doc.build(story)
    return output.getvalue()
