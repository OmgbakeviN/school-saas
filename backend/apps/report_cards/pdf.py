from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
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


TEMPLATE_DEFAULTS = {
    "CLASSIC": {
        "orientation": "PORTRAIT",
        "dense": False,
    },
    "MODERN": {
        "orientation": "PORTRAIT",
        "dense": False,
    },
    "COMPACT": {
        "orientation": "PORTRAIT",
        "dense": True,
    },
    "SECONDARY_LANDSCAPE": {
        "orientation": "LANDSCAPE",
        "dense": True,
    },
}


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


def _qr_flowable(url, size_mm=21):
    image = qrcode.make(url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return Image(
        buffer,
        width=size_mm * mm,
        height=size_mm * mm,
    )


def _template_config(payload):
    template = payload.get("template") or {}

    key = template.get("key") or "CLASSIC"
    defaults = TEMPLATE_DEFAULTS.get(
        key,
        TEMPLATE_DEFAULTS["CLASSIC"],
    )

    options = template.get("options") or {}

    return {
        "key": key,
        "name": template.get("name") or "Modèle classique",
        "version": template.get("version") or 1,
        "orientation": (
            template.get("orientation")
            or defaults["orientation"]
        ),
        "dense": defaults["dense"],
        "font_scale": float(template.get("font_scale") or 1),
        "show_rank": options.get("show_rank", True),
        "show_class_average": options.get(
            "show_class_average",
            True,
        ),
        "show_effective": options.get("show_effective", True),
        "show_decision": options.get("show_decision", True),
        "show_subject_comments": options.get(
            "show_subject_comments",
            True,
        ),
        "show_teacher_comment": options.get(
            "show_teacher_comment",
            True,
        ),
        "show_direction_comment": options.get(
            "show_direction_comment",
            True,
        ),
        "show_qr": options.get("show_qr", True),
    }


def _column_widths(
    *,
    page_width_mm,
    report_type,
    show_rank,
    show_class_average,
    show_subject_comments,
):
    if report_type == "ANNUAL":
        fixed = [20, 16, 14]
        appreciation = (
            58 if show_subject_comments else 0
        )
        subject = max(
            40,
            page_width_mm - sum(fixed) - appreciation,
        )
        widths = [subject, *fixed]
        if show_subject_comments:
            widths.append(appreciation)
        return widths

    fixed = [14, 14, 12]
    if show_rank:
        fixed.append(11)
    if show_class_average:
        fixed.append(17)

    appreciation = 55 if show_subject_comments else 0
    subject = max(
        34,
        page_width_mm - sum(fixed) - appreciation,
    )

    widths = [subject, 14, 14, 12]
    if show_rank:
        widths.append(11)
    if show_class_average:
        widths.append(17)
    if show_subject_comments:
        widths.append(appreciation)
    return widths


def _render_once(
    *,
    payload,
    verification_url,
    logo_path,
    scale,
    emergency_compact=False,
):
    output = BytesIO()
    config = _template_config(payload)

    dense = bool(config["dense"] or emergency_compact)
    orientation = config["orientation"]

    page_size = (
        landscape(A4)
        if orientation == "LANDSCAPE"
        else A4
    )

    margin = (7 if dense else 10) * mm
    bottom_margin = (7 if dense else 10) * mm

    doc = SimpleDocTemplate(
        output,
        pagesize=page_size,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=bottom_margin,
        title=f"Bulletin - {payload['student']['name']}",
        author=payload["school"]["name"],
    )

    usable_width_mm = (
        (page_size[0] - 2 * margin) / mm
    )

    primary = _hex_color(
        payload["school"].get("primary_color"),
        "#144dd2",
    )
    secondary = _hex_color(
        payload["school"].get("secondary_color"),
        "#0a0a0b",
    )

    modern = config["key"] == "MODERN"

    base_font = (7.8 if dense else 8.5) * scale
    small_font = (7.0 if dense else 7.8) * scale
    header_font = (11.0 if dense else 12.0) * scale
    title_font = (13.0 if dense else 15.0) * scale

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=title_font,
        leading=title_font * 1.15,
        alignment=TA_CENTER,
        textColor=primary,
        spaceAfter=(1 if dense else 2) * mm,
    )
    school_style = ParagraphStyle(
        "School",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=header_font,
        leading=header_font * 1.15,
        alignment=TA_CENTER,
        textColor=primary,
    )
    center_small = ParagraphStyle(
        "CenterSmall",
        parent=styles["BodyText"],
        fontSize=small_font,
        leading=small_font * 1.2,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=base_font,
        leading=base_font * 1.25,
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
            logo_size = (17 if dense else 21) * mm
            logo = Image(
                logo_path,
                width=logo_size,
                height=logo_size,
            )
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
        logo_col = 22 if dense else 27
        header = Table(
            [[logo, school_block]],
            colWidths=[
                logo_col * mm,
                (usable_width_mm - logo_col) * mm,
            ],
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#f8fbff")
                if modern
                else colors.white,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6 if modern else 0,
                primary if modern else colors.white,
            ),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(header)
    else:
        story.extend(school_block)

    spacer_small = (1.4 if dense else 2.6) * mm
    story.append(Spacer(1, spacer_small))

    title = (
        "BULLETIN ANNUEL"
        if payload["report_type"] == "ANNUAL"
        else "BULLETIN DE NOTES"
    )
    story.append(Paragraph(title, title_style))
    if payload.get("preview"):
        preview_style = ParagraphStyle(
            "Preview",
            parent=center_small,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#dc2626"),
            fontSize=(7.2 if dense else 8.2) * scale,
            leading=(8.4 if dense else 9.5) * scale,
        )
        story.append(
            Paragraph(
                "APERÇU - DOCUMENT NON OFFICIEL",
                preview_style,
            )
        )
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
    story.append(Spacer(1, spacer_small))

    student = payload["student"]
    academic = payload["academic"]

    right_label = "Effectif" if config["show_effective"] else "Cycle"
    right_value = (
        payload["summary"].get("class_size")
        if config["show_effective"]
        else academic.get("cycle")
    )

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
            Paragraph(f"<b>{right_label}</b>", label),
            Paragraph(_safe(right_value), body),
        ],
    ]

    identity_ratios = [0.16, 0.34, 0.14, 0.36]
    identity = Table(
        identity_data,
        colWidths=[
            usable_width_mm * ratio * mm
            for ratio in identity_ratios
        ],
    )
    identity.setStyle(TableStyle([
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            colors.HexColor("#cbd5e1"),
        ),
        (
            "BACKGROUND",
            (0, 0),
            (0, -1),
            colors.HexColor("#f8fafc"),
        ),
        (
            "BACKGROUND",
            (2, 0),
            (2, -1),
            colors.HexColor("#f8fafc"),
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
    ]))
    story.append(identity)
    story.append(Spacer(1, spacer_small))

    show_rank = config["show_rank"]
    show_class_average = config["show_class_average"]
    show_subject_comments = config["show_subject_comments"]

    if payload["report_type"] == "PERIOD":
        headers = [
            "Matière",
            "Moy.",
            "Barème",
            "Coef.",
        ]
        if show_rank:
            headers.append("Rang")
        if show_class_average:
            headers.append("Moy. classe")
        if show_subject_comments:
            headers.append("Appréciation")

        data = [headers]
        for row in payload.get("subjects", []):
            line = [
                Paragraph(row["subject_name"], body),
                _score(row.get("average")),
                _score(row.get("max_score")),
                _score(row.get("coefficient")),
            ]
            if show_rank:
                line.append(_safe(row.get("rank")))
            if show_class_average:
                line.append(_score(row.get("class_average")))
            if show_subject_comments:
                line.append(
                    Paragraph(
                        _safe(row.get("appreciation"), ""),
                        body,
                    )
                )
            data.append(line)
    else:
        headers = [
            "Matière",
            "Moy. annuelle",
            "Barème",
            "Coef.",
        ]
        if show_subject_comments:
            headers.append("Appréciation")

        data = [headers]
        for row in payload.get("subjects", []):
            line = [
                Paragraph(row["subject_name"], body),
                _score(row.get("average")),
                _score(row.get("max_score")),
                _score(row.get("coefficient")),
            ]
            if show_subject_comments:
                line.append(
                    Paragraph(
                        _safe(row.get("appreciation"), ""),
                        body,
                    )
                )
            data.append(line)

    width_values = _column_widths(
        page_width_mm=usable_width_mm,
        report_type=payload["report_type"],
        show_rank=show_rank,
        show_class_average=show_class_average,
        show_subject_comments=show_subject_comments,
    )

    # Normalize in case minimum widths exceed the available width.
    width_sum = sum(width_values)
    if width_sum > usable_width_mm:
        factor = usable_width_mm / width_sum
        width_values = [item * factor for item in width_values]

    table = Table(
        data,
        repeatRows=1,
        colWidths=[item * mm for item in width_values],
    )

    body_end_numeric = 3
    if show_rank:
        body_end_numeric += 1
    if show_class_average:
        body_end_numeric += 1

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            (6.6 if dense else 7.5) * scale,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.3,
            colors.HexColor("#cbd5e1"),
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (body_end_numeric, -1), "CENTER"),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                colors.white,
                colors.HexColor("#f8fafc"),
            ],
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            2.2 if dense else 4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            2.2 if dense else 4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            2.0 if dense else 4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            2.0 if dense else 4,
        ),
    ]))
    story.append(table)
    story.append(Spacer(1, spacer_small))

    summary = payload["summary"]
    summary_data = [
        [
            Paragraph("<b>Moyenne générale</b>", body),
            Paragraph(
                f"<b>{_score(summary.get('overall_average'))}</b>",
                body,
            ),
        ]
    ]

    if show_rank:
        summary_data[0].extend([
            Paragraph("<b>Rang</b>", body),
            Paragraph(
                f"<b>{_safe(summary.get('rank'))} / "
                f"{_safe(summary.get('class_size'))}</b>",
                body,
            ),
        ])
    else:
        summary_data[0].extend([
            Paragraph("<b>Barème</b>", body),
            Paragraph(
                f"<b>{_score(summary.get('default_scale'))}</b>",
                body,
            ),
        ])

    if (
        payload["report_type"] == "ANNUAL"
        and config["show_decision"]
    ):
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

    summary_widths = [
        usable_width_mm * ratio * mm
        for ratio in (0.23, 0.27, 0.22, 0.28)
    ]
    summary_table = Table(
        summary_data,
        colWidths=summary_widths,
    )
    summary_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, -1),
            colors.HexColor("#eff6ff")
            if modern
            else colors.HexColor("#f8fafc"),
        ),
        ("BOX", (0, 0), (-1, -1), 0.7, secondary),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.25,
            colors.HexColor("#bfdbfe"),
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            3 if dense else 5,
        ),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, spacer_small))

    comments = payload.get("comments", {})
    comment_blocks = []

    if (
        config["show_teacher_comment"]
        and comments.get("teacher")
    ):
        comment_blocks.append([
            Paragraph("<b>Appréciation du titulaire</b>", label),
            Paragraph(comments["teacher"], body),
        ])

    if (
        config["show_direction_comment"]
        and comments.get("general")
    ):
        comment_blocks.append([
            Paragraph("<b>Appréciation générale</b>", label),
            Paragraph(comments["general"], body),
        ])

    if comment_blocks:
        comments_table = Table(
            comment_blocks,
            colWidths=[
                usable_width_mm * 0.24 * mm,
                usable_width_mm * 0.76 * mm,
            ],
        )
        comments_table.setStyle(TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#cbd5e1"),
            ),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#f8fafc"),
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3 if dense else 5,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3 if dense else 5,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3 if dense else 5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3 if dense else 5,
            ),
        ]))
        story.append(comments_table)
        story.append(Spacer(1, spacer_small))

    signatures = payload.get("signatures", {})
    signature_breaks = "<br/><br/>" if dense else "<br/><br/><br/>"

    sign_table = Table(
        [[
            Paragraph(
                "<b>Titulaire / responsable</b>"
                + signature_breaks
                + _safe(signatures.get("class_teacher"), ""),
                center_small,
            ),
            Paragraph(
                "<b>Direction</b>"
                + signature_breaks
                + _safe(signatures.get("publisher"), ""),
                center_small,
            ),
        ]],
        colWidths=[
            usable_width_mm * 0.5 * mm,
            usable_width_mm * 0.5 * mm,
        ],
    )
    sign_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
    ]))
    story.append(KeepTogether(sign_table))

    if config["show_qr"]:
        story.append(Spacer(1, spacer_small))
        qr_size = 17 if dense else 21
        qr = _qr_flowable(
            verification_url,
            size_mm=qr_size,
        )
        verification_text = Paragraph(
            "<b>Document officiel vérifiable</b><br/>"
            f"Version {payload['version']}<br/>"
            f"Empreinte : "
            f"{payload['verification']['fingerprint']}<br/>"
            "Scannez le QR code pour vérifier l'authenticité.",
            body,
        )
        qr_col = qr_size + 3
        verification_table = Table(
            [[verification_text, qr]],
            colWidths=[
                (usable_width_mm - qr_col) * mm,
                qr_col * mm,
            ],
        )
        verification_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#f8fafc"),
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#cbd5e1"),
            ),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4 if dense else 6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4 if dense else 6,
            ),
        ]))
        story.append(KeepTogether(verification_table))

    doc.build(story)

    return {
        "pdf_bytes": output.getvalue(),
        "page_count": int(getattr(doc, "page", 1) or 1),
        "scale": scale,
        "emergency_compact": emergency_compact,
        "orientation": orientation,
    }


def generate_report_card_pdf(
    *,
    payload,
    verification_url,
    logo_path=None,
    return_meta=False,
):
    """
    Render an official report card and try to keep it on exactly one A4 sheet.

    The selected template is tried first. If it overflows, the renderer
    automatically tightens spacing and font size within a safe range.
    Publication code must reject the result when `fits_one_page` is False.
    """
    config = _template_config(payload)
    requested_scale = max(
        0.80,
        min(1.10, float(config["font_scale"])),
    )

    attempts = [
        (requested_scale, config["dense"]),
        (max(0.78, requested_scale * 0.94), True),
        (max(0.74, requested_scale * 0.88), True),
        (0.72, True),
    ]

    seen = set()
    result = None

    for scale, compact in attempts:
        key = (round(scale, 3), bool(compact))
        if key in seen:
            continue
        seen.add(key)

        result = _render_once(
            payload=payload,
            verification_url=verification_url,
            logo_path=logo_path,
            scale=scale,
            emergency_compact=compact,
        )

        if result["page_count"] == 1:
            result["fits_one_page"] = True
            break
    else:
        result["fits_one_page"] = False

    if return_meta:
        return result

    return result["pdf_bytes"]
