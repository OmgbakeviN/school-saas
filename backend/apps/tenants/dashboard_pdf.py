from io import BytesIO
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FR = {
    "dashboard_title": "Rapport statistique de l'établissement",
    "class_title": "Rapport statistique de classe",
    "academic_year": "Année scolaire",
    "active_period": "Période courante",
    "generated": "Généré le",
    "scope_school": "Périmètre : établissement",
    "scope_teacher": "Périmètre : classes de l'enseignant",
    "students": "Élèves",
    "classes": "Classes",
    "teachers": "Enseignants",
    "members": "Membres",
    "collection_rate": "Taux de recouvrement",
    "publication_rate": "Taux de publication",
    "published_assessments": "Évaluations publiées",
    "overview": "Vue d'ensemble",
    "population": "Population scolaire",
    "gender": "Répartition par genre",
    "cycles": "Répartition par cycle",
    "class_load": "Effectifs par classe",
    "name": "Nom",
    "count": "Effectif",
    "percentage": "%",
    "capacity": "Capacité",
    "occupancy": "Occupation",
    "male": "Garçons",
    "female": "Filles",
    "other": "Autre",
    "unknown": "Non renseigné",
    "academics": "Activité pédagogique",
    "status": "Statut",
    "report_cards": "Bulletins publiés",
    "annual_average": "Moyenne annuelle",
    "draft": "Brouillon",
    "input": "Saisie en cours",
    "submitted": "Soumis",
    "validated": "Validé",
    "published": "Publié",
    "finance": "Situation financière",
    "expected": "Pension attendue",
    "collected": "Total encaissé",
    "outstanding": "Reste à encaisser",
    "accounts": "Comptes pension",
    "paid": "Soldés",
    "partial": "Partiels",
    "unpaid": "Impayés",
    "monthly": "Encaissements des 6 derniers mois",
    "month": "Mois",
    "amount": "Montant",
    "classroom": "Classe",
    "level": "Niveau",
    "cycle": "Cycle",
    "section": "Section",
    "teaching_team": "Équipe pédagogique",
    "teacher": "Enseignant",
    "subjects": "Matières",
    "leadership": "Responsabilité",
    "subject_performance": "Performance par matière",
    "subject": "Matière",
    "average_on_20": "Moyenne /20",
    "scores_count": "Notes prises en compte",
    "promotion": "Décisions de fin d'année",
    "decision": "Décision",
    "financial_class": "Situation financière de la classe",
    "payments_today": "Paiements aujourd'hui",
}

EN = {
    "dashboard_title": "School Statistics Report",
    "class_title": "Class Statistics Report",
    "academic_year": "Academic Year",
    "active_period": "Current Period",
    "generated": "Generated",
    "scope_school": "Scope: whole institution",
    "scope_teacher": "Scope: teacher's classes",
    "students": "Students",
    "classes": "Classes",
    "teachers": "Teachers",
    "members": "Members",
    "collection_rate": "Collection Rate",
    "publication_rate": "Publication Rate",
    "published_assessments": "Published Assessments",
    "overview": "Overview",
    "population": "School Population",
    "gender": "Gender Distribution",
    "cycles": "Students by Cycle",
    "class_load": "Class Enrollment",
    "name": "Name",
    "count": "Count",
    "percentage": "%",
    "capacity": "Capacity",
    "occupancy": "Occupancy",
    "male": "Boys",
    "female": "Girls",
    "other": "Other",
    "unknown": "Not specified",
    "academics": "Academic Activity",
    "status": "Status",
    "report_cards": "Published Report Cards",
    "annual_average": "Annual Average",
    "draft": "Draft",
    "input": "Score Entry",
    "submitted": "Submitted",
    "validated": "Validated",
    "published": "Published",
    "finance": "Financial Overview",
    "expected": "Expected Tuition",
    "collected": "Collected",
    "outstanding": "Outstanding",
    "accounts": "Tuition Accounts",
    "paid": "Paid",
    "partial": "Partial",
    "unpaid": "Unpaid",
    "monthly": "Collections over the Last 6 Months",
    "month": "Month",
    "amount": "Amount",
    "classroom": "Class",
    "level": "Level",
    "cycle": "Cycle",
    "section": "Section",
    "teaching_team": "Teaching Team",
    "teacher": "Teacher",
    "subjects": "Subjects",
    "leadership": "Responsibility",
    "subject_performance": "Subject Performance",
    "subject": "Subject",
    "average_on_20": "Average /20",
    "scores_count": "Grades Included",
    "promotion": "End-of-Year Decisions",
    "decision": "Decision",
    "financial_class": "Class Financial Status",
    "payments_today": "Payments Today",
}


def _labels(language):
    return EN if str(language or "").lower().startswith("en") else FR


def _hex(value, fallback):
    value = str(value or "").strip()
    return value if re.match(r"^#[0-9a-fA-F]{6}$", value) else fallback


def _rl_color(value, fallback="#144dd2"):
    return colors.HexColor(_hex(value, fallback))


def _money(value, currency="XAF"):
    try:
        amount = float(value or 0)
        formatted = f"{amount:,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        formatted = str(value or "0")
    return f"{formatted} {currency or 'XAF'}"


def _number(value):
    if value in (None, ""):
        return "—"
    try:
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _date_time(value):
    if not value:
        return "—"
    try:
        return value.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


def _school_logo(school, max_width=18 * mm, max_height=18 * mm):
    logo = getattr(school, "logo", None)
    if not logo:
        return None
    try:
        path = Path(logo.path)
        if not path.exists():
            return None
        img = Image(str(path))
        iw, ih = img.imageWidth, img.imageHeight
        scale = min(max_width / iw, max_height / ih)
        img.drawWidth = iw * scale
        img.drawHeight = ih * scale
        return img
    except Exception:
        return None


class MetricCard(Flowable):
    def __init__(self, label, value, primary, width=42 * mm, height=21 * mm):
        super().__init__()
        self.width = width
        self.height = height
        self.label = str(label)
        self.value = str(value)
        self.primary = primary

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(colors.white)
        canvas.setStrokeColor(
            colors.Color(
                self.primary.red,
                self.primary.green,
                self.primary.blue,
                alpha=0.20,
            )
        )
        canvas.roundRect(
            0, 0, self.width, self.height, 5 * mm,
            fill=1, stroke=1
        )
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(
            4 * mm,
            self.height - 6 * mm,
            self.label[:42],
        )
        canvas.setFillColor(self.primary)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(4 * mm, 5 * mm, self.value[:26])
        canvas.restoreState()


def _styles(primary):
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=colors.HexColor("#172033"),
            spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=2 * mm,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=primary,
            spaceBefore=5 * mm,
            spaceAfter=2.5 * mm,
        ),
        "normal": ParagraphStyle(
            "Normal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#64748b"),
        ),
    }


def _table(data, primary, widths=None, font_size=7.5):
    table = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        (
            "BACKGROUND", (0, 0), (-1, 0),
            colors.Color(
                primary.red,
                primary.green,
                primary.blue,
                alpha=0.10,
            ),
        ),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        (
            "ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.white, colors.HexColor("#f8fafc")],
        ),
    ]))
    return table


def _header_story(story, *, school, title, subtitle, primary, styles, width):
    logo = _school_logo(school)
    name = getattr(school, "name", "BE WISE School")
    motto = getattr(school, "motto", "") or ""

    identity = [
        Paragraph(f"<b>{name}</b>", styles["normal"]),
        Paragraph(motto, styles["small"])
        if motto
        else Spacer(1, 1),
    ]
    header = Table(
        [[logo or "", identity]],
        colWidths=[22 * mm, width - 22 * mm],
        hAlign="LEFT",
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([
        header,
        Spacer(1, 3 * mm),
        Table(
            [[""]],
            colWidths=[width],
            rowHeights=[1.3 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), primary)
            ]),
        ),
        Spacer(1, 4 * mm),
        Paragraph(title, styles["title"]),
        Paragraph(subtitle, styles["subtitle"]),
    ])


def _page_decorator(school, primary):
    def draw(canvas, doc):
        canvas.saveState()
        width, _ = doc.pagesize
        canvas.setStrokeColor(
            colors.Color(
                primary.red,
                primary.green,
                primary.blue,
                alpha=0.18,
            )
        )
        canvas.line(15 * mm, 13 * mm, width - 15 * mm, 13 * mm)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(
            15 * mm,
            8 * mm,
            str(getattr(school, "name", "BE WISE School")),
        )
        canvas.drawRightString(
            width - 15 * mm,
            8 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()
    return draw


def generate_dashboard_statistics_pdf(*, school, analytics, language="fr"):
    labels = _labels(language)
    primary = _rl_color(getattr(school, "primary_color", None))
    styles = _styles(primary)
    buffer = BytesIO()

    usable_width = 174 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title=labels["dashboard_title"],
        author=str(getattr(school, "name", "BE WISE School")),
    )
    story = []

    year = analytics.get("academic_year") or {}
    period = analytics.get("active_period") or {}
    scope = (
        labels["scope_teacher"]
        if analytics.get("scope") == "TEACHER"
        else labels["scope_school"]
    )
    subtitle = " · ".join(
        item for item in [
            scope,
            f'{labels["academic_year"]}: {year.get("name") or "—"}',
            (
                f'{labels["active_period"]}: {period.get("name")}'
                if period.get("name")
                else None
            ),
            f'{labels["generated"]}: {_date_time(analytics.get("generated_at"))}',
        ] if item
    )
    _header_story(
        story,
        school=school,
        title=labels["dashboard_title"],
        subtitle=subtitle,
        primary=primary,
        styles=styles,
        width=usable_width,
    )

    overview = analytics.get("overview") or {}
    finance = analytics.get("finance")
    academics = analytics.get("academics")

    cards = [
        MetricCard(labels["students"], _number(overview.get("students")), primary),
        MetricCard(labels["classes"], _number(overview.get("classes")), primary),
        MetricCard(labels["teachers"], _number(overview.get("teachers")), primary),
    ]
    if finance:
        cards.append(
            MetricCard(
                labels["collection_rate"],
                f'{_number(finance.get("collection_rate"))}%',
                primary,
            )
        )
    elif academics:
        cards.append(
            MetricCard(
                labels["published_assessments"],
                f'{_number(academics.get("published_assessments"))}/'
                f'{_number(academics.get("assessments_total"))}',
                primary,
            )
        )
    else:
        cards.append(
            MetricCard(
                labels["members"],
                _number(overview.get("members")),
                primary,
            )
        )

    story.extend([
        Paragraph(labels["overview"], styles["section"]),
        Table([cards], colWidths=[43 * mm] * 4, hAlign="LEFT"),
    ])

    population = analytics.get("population") or {}
    gender_rows = population.get("gender") or []
    story.append(Paragraph(labels["population"], styles["section"]))

    if gender_rows:
        gender_label = {
            "MALE": labels["male"],
            "FEMALE": labels["female"],
            "OTHER": labels["other"],
            "UNKNOWN": labels["unknown"],
        }
        data = [[labels["gender"], labels["count"], labels["percentage"]]]
        for row in gender_rows:
            data.append([
                gender_label.get(row.get("key"), row.get("key")),
                _number(row.get("count")),
                f'{_number(row.get("percentage"))}%',
            ])
        story.append(
            _table(data, primary, [85 * mm, 40 * mm, 40 * mm])
        )

    cycles = population.get("cycles") or []
    if cycles:
        story.append(Paragraph(labels["cycles"], styles["section"]))
        data = [[
            labels["name"],
            labels["section"],
            labels["count"],
            labels["percentage"],
        ]]
        for row in cycles:
            data.append([
                row.get("name") or "—",
                row.get("section_name") or "—",
                _number(row.get("count")),
                f'{_number(row.get("percentage"))}%',
            ])
        story.append(
            _table(data, primary, [62 * mm, 52 * mm, 24 * mm, 27 * mm])
        )

    classrooms = population.get("classrooms") or []
    if classrooms:
        story.append(Paragraph(labels["class_load"], styles["section"]))
        data = [[
            labels["classroom"],
            labels["level"],
            labels["count"],
            labels["capacity"],
            labels["occupancy"],
        ]]
        for row in classrooms:
            data.append([
                row.get("name") or "—",
                row.get("level_name") or "—",
                _number(row.get("count")),
                _number(row.get("capacity")),
                (
                    f'{_number(row.get("occupancy_rate"))}%'
                    if row.get("occupancy_rate") is not None
                    else "—"
                ),
            ])
        story.append(
            _table(
                data,
                primary,
                [47 * mm, 43 * mm, 22 * mm, 24 * mm, 29 * mm],
            )
        )

    if academics:
        story.append(Paragraph(labels["academics"], styles["section"]))
        academic_cards = [
            MetricCard(
                labels["published_assessments"],
                f'{_number(academics.get("published_assessments"))}/'
                f'{_number(academics.get("assessments_total"))}',
                primary,
                53 * mm,
                20 * mm,
            ),
            MetricCard(
                labels["report_cards"],
                _number(academics.get("published_report_cards")),
                primary,
                53 * mm,
                20 * mm,
            ),
            MetricCard(
                labels["annual_average"],
                _number(academics.get("annual_average")),
                primary,
                53 * mm,
                20 * mm,
            ),
        ]
        story.append(
            Table(
                [academic_cards],
                colWidths=[54 * mm] * 3,
                hAlign="LEFT",
            )
        )

        statuses = academics.get("statuses") or []
        if statuses:
            status_label = {
                "DRAFT": labels["draft"],
                "INPUT": labels["input"],
                "SUBMITTED": labels["submitted"],
                "VALIDATED": labels["validated"],
                "PUBLISHED": labels["published"],
            }
            data = [[labels["status"], labels["count"], labels["percentage"]]]
            for row in statuses:
                data.append([
                    status_label.get(row.get("key"), row.get("key")),
                    _number(row.get("count")),
                    f'{_number(row.get("percentage"))}%',
                ])
            story.extend([
                Spacer(1, 2 * mm),
                _table(data, primary, [95 * mm, 34 * mm, 36 * mm]),
            ])

    if finance:
        story.append(Paragraph(labels["finance"], styles["section"]))
        currency = finance.get("currency") or "XAF"
        data = [
            [labels["expected"], _money(finance.get("expected_total"), currency)],
            [labels["collected"], _money(finance.get("collected_total"), currency)],
            [labels["outstanding"], _money(finance.get("outstanding_total"), currency)],
            [labels["collection_rate"], f'{_number(finance.get("collection_rate"))}%'],
            [labels["accounts"], _number(finance.get("accounts_count"))],
            [labels["paid"], _number(finance.get("paid_count"))],
            [labels["partial"], _number(finance.get("partial_count"))],
            [labels["unpaid"], _number(finance.get("unpaid_count"))],
        ]
        story.append(
            _table(
                [[labels["finance"], ""]] + data,
                primary,
                [90 * mm, 75 * mm],
            )
        )

        monthly = finance.get("monthly_collections") or []
        if monthly:
            story.append(Paragraph(labels["monthly"], styles["section"]))
            data = [[labels["month"], labels["amount"]]]
            for row in monthly:
                data.append([
                    f'{int(row.get("month")):02d}/{row.get("year")}',
                    _money(row.get("amount"), currency),
                ])
            story.append(
                _table(data, primary, [82 * mm, 82 * mm])
            )

    doc.build(
        story,
        onFirstPage=_page_decorator(school, primary),
        onLaterPages=_page_decorator(school, primary),
    )
    return buffer.getvalue()


def generate_classroom_statistics_pdf(*, school, statistics, language="fr"):
    labels = _labels(language)
    primary = _rl_color(getattr(school, "primary_color", None))
    styles = _styles(primary)
    buffer = BytesIO()

    page_width, _ = landscape(A4)
    usable_width = page_width - 30 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=13 * mm,
        bottomMargin=17 * mm,
        title=labels["class_title"],
        author=str(getattr(school, "name", "BE WISE School")),
    )

    classroom = statistics.get("classroom") or {}
    year = classroom.get("academic_year") or {}
    period = statistics.get("active_period") or {}
    subtitle = " · ".join(
        item for item in [
            f'{labels["classroom"]}: {classroom.get("name") or "—"}',
            f'{labels["academic_year"]}: {year.get("name") or "—"}',
            (
                f'{labels["active_period"]}: {period.get("name")}'
                if period.get("name")
                else None
            ),
            f'{labels["generated"]}: {_date_time(statistics.get("generated_at"))}',
        ] if item
    )

    story = []
    _header_story(
        story,
        school=school,
        title=labels["class_title"],
        subtitle=subtitle,
        primary=primary,
        styles=styles,
        width=usable_width,
    )

    class_meta = [
        [labels["classroom"], classroom.get("name") or "—"],
        [labels["level"], (classroom.get("level") or {}).get("name") or "—"],
        [labels["cycle"], (classroom.get("cycle") or {}).get("name") or "—"],
        [labels["section"], (classroom.get("section") or {}).get("name") or "—"],
    ]
    story.append(
        _table(
            [[labels["overview"], ""]] + class_meta,
            primary,
            [55 * mm, 115 * mm],
        )
    )

    population = statistics.get("population") or {}
    teaching = statistics.get("teaching") or {}
    cards = [
        MetricCard(labels["students"], _number(population.get("students")), primary, 55*mm, 20*mm),
        MetricCard(labels["capacity"], _number(population.get("capacity")), primary, 55*mm, 20*mm),
        MetricCard(
            labels["occupancy"],
            (
                f'{_number(population.get("occupancy_rate"))}%'
                if population.get("occupancy_rate") is not None
                else "—"
            ),
            primary,
            55*mm,
            20*mm,
        ),
        MetricCard(labels["teachers"], _number(teaching.get("teachers_count")), primary, 55*mm, 20*mm),
    ]
    story.extend([
        Paragraph(labels["population"], styles["section"]),
        Table([cards], colWidths=[57 * mm] * 4, hAlign="LEFT"),
    ])

    gender = population.get("gender") or []
    if gender:
        label_map = {
            "MALE": labels["male"],
            "FEMALE": labels["female"],
            "OTHER": labels["other"],
            "UNKNOWN": labels["unknown"],
        }
        data = [[labels["gender"], labels["count"], labels["percentage"]]]
        for row in gender:
            data.append([
                label_map.get(row.get("key"), row.get("key")),
                _number(row.get("count")),
                f'{_number(row.get("percentage"))}%',
            ])
        story.extend([
            Spacer(1, 2 * mm),
            _table(data, primary, [90 * mm, 45 * mm, 45 * mm]),
        ])

    teachers = teaching.get("teachers") or []
    if teachers:
        story.append(Paragraph(labels["teaching_team"], styles["section"]))
        data = [[
            labels["teacher"],
            labels["subjects"],
            labels["leadership"],
        ]]
        for teacher in teachers:
            data.append([
                teacher.get("name") or "—",
                ", ".join(
                    item.get("name") or ""
                    for item in teacher.get("subjects") or []
                ) or "—",
                ", ".join(
                    item.get("label") or ""
                    for item in teacher.get("leadership_roles") or []
                ) or "—",
            ])
        story.append(
            _table(
                data,
                primary,
                [72 * mm, 105 * mm, 75 * mm],
                font_size=7.2,
            )
        )

    academics = statistics.get("academics")
    if academics:
        story.append(Paragraph(labels["academics"], styles["section"]))
        academic_cards = [
            MetricCard(
                labels["published_assessments"],
                f'{_number(academics.get("published_assessments"))}/'
                f'{_number(academics.get("assessments_total"))}',
                primary, 55*mm, 20*mm,
            ),
            MetricCard(
                labels["publication_rate"],
                f'{_number(academics.get("publication_rate"))}%',
                primary, 55*mm, 20*mm,
            ),
            MetricCard(
                labels["report_cards"],
                _number(academics.get("published_report_cards")),
                primary, 55*mm, 20*mm,
            ),
            MetricCard(
                labels["annual_average"],
                _number(academics.get("annual_average")),
                primary, 55*mm, 20*mm,
            ),
        ]
        story.append(
            Table(
                [academic_cards],
                colWidths=[57 * mm] * 4,
                hAlign="LEFT",
            )
        )

        statuses = academics.get("statuses") or []
        if statuses:
            status_label = {
                "DRAFT": labels["draft"],
                "INPUT": labels["input"],
                "SUBMITTED": labels["submitted"],
                "VALIDATED": labels["validated"],
                "PUBLISHED": labels["published"],
            }
            data = [[labels["status"], labels["count"], labels["percentage"]]]
            for row in statuses:
                data.append([
                    status_label.get(row.get("key"), row.get("key")),
                    _number(row.get("count")),
                    f'{_number(row.get("percentage"))}%',
                ])
            story.extend([
                Spacer(1, 2 * mm),
                _table(data, primary, [95 * mm, 45 * mm, 45 * mm]),
            ])

        subjects = academics.get("subjects") or []
        if subjects:
            story.append(
                Paragraph(labels["subject_performance"], styles["section"])
            )
            data = [[
                labels["subject"],
                labels["average_on_20"],
                labels["scores_count"],
            ]]
            for row in subjects:
                data.append([
                    row.get("name") or "—",
                    _number(row.get("average_on_20")),
                    _number(row.get("scores_count")),
                ])
            story.append(
                _table(data, primary, [125 * mm, 55 * mm, 55 * mm])
            )

        decisions = academics.get("promotion_decisions") or []
        if decisions:
            decision_fr = {
                "PENDING": "En attente",
                "PROMOTED": "Admis / promus",
                "REPEATED": "Redoublants",
                "GRADUATED": "Diplômés",
                "TRANSFERRED": "Transférés",
                "WITHDRAWN": "Retirés",
            }
            decision_en = {
                "PENDING": "Pending",
                "PROMOTED": "Promoted",
                "REPEATED": "Repeat",
                "GRADUATED": "Graduated",
                "TRANSFERRED": "Transferred",
                "WITHDRAWN": "Withdrawn",
            }
            decision_map = (
                decision_en
                if str(language).lower().startswith("en")
                else decision_fr
            )
            story.append(Paragraph(labels["promotion"], styles["section"]))
            data = [[labels["decision"], labels["count"]]]
            for row in decisions:
                data.append([
                    decision_map.get(row.get("key"), row.get("key")),
                    _number(row.get("count")),
                ])
            story.append(
                _table(data, primary, [140 * mm, 55 * mm])
            )

    finance = statistics.get("finance")
    if finance:
        story.append(
            Paragraph(labels["financial_class"], styles["section"])
        )
        currency = finance.get("currency") or "XAF"
        data = [
            [labels["expected"], _money(finance.get("expected_total"), currency)],
            [labels["collected"], _money(finance.get("collected_total"), currency)],
            [labels["outstanding"], _money(finance.get("outstanding_total"), currency)],
            [labels["collection_rate"], f'{_number(finance.get("collection_rate"))}%'],
            [labels["accounts"], _number(finance.get("accounts_count"))],
            [labels["paid"], _number(finance.get("paid_count"))],
            [labels["partial"], _number(finance.get("partial_count"))],
            [labels["unpaid"], _number(finance.get("unpaid_count"))],
            [labels["payments_today"], _money(finance.get("payments_today"), currency)],
        ]
        story.append(
            _table(
                [[labels["finance"], ""]] + data,
                primary,
                [100 * mm, 90 * mm],
            )
        )

    doc.build(
        story,
        onFirstPage=_page_decorator(school, primary),
        onLaterPages=_page_decorator(school, primary),
    )
    return buffer.getvalue()
