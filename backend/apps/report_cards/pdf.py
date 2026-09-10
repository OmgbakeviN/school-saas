from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _hex_color(value, fallback):
    try:
        return colors.HexColor(value or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _safe(value, fallback="-"):
    if value in (None, ""):
        return fallback
    return str(value)


def _score(value):
    if value in (None, ""):
        return "-"
    try:
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def _qr_flowable(url):
    image = qrcode.make(url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return Image(buffer, width=25 * mm, height=25 * mm)


def generate_report_card_pdf(
    *,
    payload,
    verification_url,
    logo_path=None,
):
    """
    Génère le PDF officiel depuis un payload déjà figé.

    Le PDF ne relit aucune note dans la base : il représente uniquement
    le snapshot immuable fourni.
    """
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title=f"Bulletin - {payload['student']['name']}",
        author=payload["school"]["name"],
    )

    primary = _hex_color(
        payload["school"].get("primary_color"),
        "#0f172a",
    )
    secondary = _hex_color(
        payload["school"].get("secondary_color"),
        "#2563eb",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=primary,
        spaceAfter=2 * mm,
    )
    school_style = ParagraphStyle(
        "School",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=primary,
    )
    center_small = ParagraphStyle(
        "CenterSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )
    label = ParagraphStyle(
        "Label",
        parent=body,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#475569"),
    )

    story = []

    logo = None
    if logo_path:
        try:
            logo = Image(logo_path, width=22 * mm, height=22 * mm)
        except Exception:
            logo = None

    school_block = [
        Paragraph(payload["school"]["name"], school_style),
        Paragraph(
            _safe(payload["school"].get("motto"), ""),
            center_small,
        ),
        Paragraph(
            " - ".join(
                item
                for item in [
                    payload["school"].get("city"),
                    payload["school"].get("country"),
                    payload["school"].get("phone"),
                ]
                if item
            ),
            center_small,
        ),
    ]

    if logo:
        header = Table(
            [[logo, school_block]],
            colWidths=[28 * mm, 145 * mm],
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ]))
        story.append(header)
    else:
        story.extend(school_block)

    story.append(Spacer(1, 3 * mm))
    title = (
        "BULLETIN ANNUEL"
        if payload["report_type"] == "ANNUAL"
        else "BULLETIN DE NOTES"
    )
    story.append(Paragraph(title, title_style))
    story.append(
        Paragraph(
            f"Année scolaire : {payload['academic_year']['name']}"
            + (
                f" - {payload['period']['name']}"
                if payload.get("period")
                else ""
            ),
            center_small,
        )
    )
    story.append(Spacer(1, 4 * mm))

    student = payload["student"]
    academic = payload["academic"]
    identity_data = [
        [
            Paragraph("<b>Élève</b>", label),
            Paragraph(student["name"], body),
            Paragraph("<b>Matricule</b>", label),
            Paragraph(_safe(student.get("matricule")), body),
        ],
        [
            Paragraph("<b>Classe</b>", label),
            Paragraph(academic["classroom"], body),
            Paragraph("<b>Niveau</b>", label),
            Paragraph(academic["level"], body),
        ],
        [
            Paragraph("<b>Titulaire / responsable</b>", label),
            Paragraph(_safe(academic.get("class_teacher")), body),
            Paragraph("<b>Effectif</b>", label),
            Paragraph(_safe(payload["summary"].get("class_size")), body),
        ],
    ]
    identity = Table(
        identity_data,
        colWidths=[30 * mm, 62 * mm, 26 * mm, 55 * mm],
    )
    identity.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(identity)
    story.append(Spacer(1, 4 * mm))

    if payload["report_type"] == "PERIOD":
        headers = [
            "Matière",
            "Moy.",
            "Barème",
            "Coef.",
            "Rang",
            "Moy. classe",
            "Appréciation",
        ]
        data = [headers]
        for row in payload.get("subjects", []):
            data.append([
                Paragraph(row["subject_name"], body),
                _score(row.get("average")),
                _score(row.get("max_score")),
                _score(row.get("coefficient")),
                _safe(row.get("rank")),
                _score(row.get("class_average")),
                Paragraph(_safe(row.get("appreciation"), ""), body),
            ])

        table = Table(
            data,
            repeatRows=1,
            colWidths=[
                39 * mm,
                15 * mm,
                15 * mm,
                13 * mm,
                12 * mm,
                19 * mm,
                60 * mm,
            ],
        )
    else:
        headers = [
            "Matière",
            "Moy. annuelle",
            "Barème",
            "Coef.",
            "Appréciation",
        ]
        data = [headers]
        for row in payload.get("subjects", []):
            data.append([
                Paragraph(row["subject_name"], body),
                _score(row.get("average")),
                _score(row.get("max_score")),
                _score(row.get("coefficient")),
                Paragraph(_safe(row.get("appreciation"), ""), body),
            ])
        table = Table(
            data,
            repeatRows=1,
            colWidths=[50 * mm, 25 * mm, 20 * mm, 18 * mm, 60 * mm],
        )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (5, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#f8fafc"),
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))

    summary = payload["summary"]
    summary_data = [
        [
            Paragraph("<b>Moyenne générale</b>", body),
            Paragraph(
                f"<b>{_score(summary.get('overall_average'))}</b>",
                body,
            ),
            Paragraph("<b>Rang</b>", body),
            Paragraph(
                f"<b>{_safe(summary.get('rank'))} / "
                f"{_safe(summary.get('class_size'))}</b>",
                body,
            ),
        ]
    ]
    if payload["report_type"] == "ANNUAL":
        summary_data.append([
            Paragraph("<b>Décision</b>", body),
            Paragraph(
                _safe(summary.get("promotion_decision_label")),
                body,
            ),
            Paragraph("<b>Moyenne annuelle</b>", body),
            Paragraph(
                f"<b>{_score(summary.get('overall_average'))}</b>",
                body,
            ),
        ])

    summary_table = Table(
        summary_data,
        colWidths=[40 * mm, 45 * mm, 40 * mm, 48 * mm],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 0.8, secondary),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bfdbfe")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4 * mm))

    comments = payload.get("comments", {})
    comment_blocks = []
    if comments.get("teacher"):
        comment_blocks.append([
            Paragraph("<b>Appréciation du titulaire</b>", label),
            Paragraph(comments["teacher"], body),
        ])
    if comments.get("general"):
        comment_blocks.append([
            Paragraph("<b>Appréciation générale</b>", label),
            Paragraph(comments["general"], body),
        ])
    if comment_blocks:
        comments_table = Table(
            comment_blocks,
            colWidths=[42 * mm, 131 * mm],
        )
        comments_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(comments_table)
        story.append(Spacer(1, 4 * mm))

    signatures = payload.get("signatures", {})
    sign_table = Table(
        [[
            Paragraph(
                "<b>Titulaire / responsable</b><br/><br/><br/>"
                + _safe(signatures.get("class_teacher"), ""),
                center_small,
            ),
            Paragraph(
                "<b>Direction</b><br/><br/><br/>"
                + _safe(signatures.get("publisher"), ""),
                center_small,
            ),
        ]],
        colWidths=[86 * mm, 86 * mm],
    )
    sign_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
    ]))
    story.append(KeepTogether(sign_table))
    story.append(Spacer(1, 4 * mm))

    qr = _qr_flowable(verification_url)
    verification_text = Paragraph(
        "<b>Document officiel vérifiable</b><br/>"
        f"Version {payload['version']}<br/>"
        f"Empreinte : {payload['verification']['fingerprint']}<br/>"
        "Scannez le QR code pour vérifier l'authenticité.",
        body,
    )
    verification_table = Table(
        [[verification_text, qr]],
        colWidths=[145 * mm, 27 * mm],
    )
    verification_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(KeepTogether(verification_table))

    doc.build(story)
    return output.getvalue()
