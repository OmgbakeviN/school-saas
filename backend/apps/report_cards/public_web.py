import hashlib
import re
from html import escape
from urllib.parse import quote


HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


FR = {
    "page_title": "Résultats officiels",
    "verified": "Bulletin authentique",
    "official": "Version web du bulletin officiel",
    "student": "Élève",
    "student_id": "Matricule",
    "classroom": "Classe",
    "level": "Niveau",
    "year": "Année scolaire",
    "period": "Période",
    "annual": "Bulletin annuel",
    "subject": "Matière",
    "average": "Moyenne",
    "scale": "Barème",
    "coefficient": "Coef.",
    "rank": "Rang",
    "class_average": "Moy. classe",
    "comment": "Appréciation",
    "overall": "Moyenne générale",
    "class_rank": "Rang de classe",
    "class_size": "Effectif",
    "decision": "Décision",
    "teacher_comment": "Appréciation du titulaire",
    "management_comment": "Appréciation générale",
    "verification": "Vérification",
    "version": "Version",
    "published": "Publié le",
    "fingerprint": "Empreinte",
    "print": "Imprimer",
    "secured": "Les résultats affichés correspondent à la version publiée liée à ce QR code.",
    "no_subjects": "Aucun résultat de matière n'est disponible dans cette version.",
}

EN = {
    "page_title": "Official Results",
    "verified": "Authentic report card",
    "official": "Web version of the official report card",
    "student": "Student",
    "student_id": "Student ID",
    "classroom": "Class",
    "level": "Level",
    "year": "Academic Year",
    "period": "Period",
    "annual": "Annual Report Card",
    "subject": "Subject",
    "average": "Average",
    "scale": "Scale",
    "coefficient": "Coeff.",
    "rank": "Rank",
    "class_average": "Class Average",
    "comment": "Comment",
    "overall": "Overall Average",
    "class_rank": "Class Rank",
    "class_size": "Class Size",
    "decision": "Decision",
    "teacher_comment": "Class Teacher Comment",
    "management_comment": "School Administration Comment",
    "verification": "Verification",
    "version": "Version",
    "published": "Published",
    "fingerprint": "Fingerprint",
    "print": "Print",
    "secured": "The results shown correspond to the published version linked to this QR code.",
    "no_subjects": "No subject results are available in this version.",
}


def _color(value, fallback):
    candidate = str(value or "").strip()
    return candidate if HEX_RE.match(candidate) else fallback


def _fmt(value):
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _absolute_url(request, value):
    if not value:
        return ""
    value = str(value)
    if value.startswith(("http://", "https://")):
        return value
    try:
        return request.build_absolute_uri(value)
    except Exception:
        return value


def _school_logo_url(request, school):
    if getattr(school, "logo", None):
        try:
            return _absolute_url(request, school.logo.url)
        except Exception:
            pass
    return getattr(school, "logo_url", "") or ""


def _student_photo_url(request, snapshot, payload):
    photo_meta = (payload.get("student") or {}).get("photo") or {}
    expected_hash = photo_meta.get("sha256")
    if not photo_meta.get("included") or not expected_hash:
        return ""

    student = snapshot.enrollment.student
    if not getattr(student, "photo", None):
        return ""

    try:
        with student.photo.open("rb") as handle:
            current_hash = hashlib.sha256(handle.read()).hexdigest()
        if current_hash != expected_hash:
            return ""
        return _absolute_url(request, student.photo.url)
    except Exception:
        return ""


def _period_name(payload, labels):
    period = payload.get("period")
    if period and period.get("name"):
        name = str(period["name"])
        if labels is EN:
            patterns = (
                (r"(?i)^trimestre\s*(\d+)$", r"Term \1"),
                (r"(?i)^semestre\s*(\d+)$", r"Semester \1"),
                (r"(?i)^séquence\s*(\d+)$", r"Sequence \1"),
                (r"(?i)^sequence\s*(\d+)$", r"Sequence \1"),
            )
            for pattern, repl in patterns:
                if re.match(pattern, name.strip()):
                    return re.sub(pattern, repl, name.strip())
        return name
    return labels["annual"]


def _subject_rows(payload, labels):
    options = ((payload.get("template") or {}).get("options") or {})
    show_rank = options.get("show_rank", True)
    show_class_average = options.get("show_class_average", True)
    show_comments = options.get("show_subject_comments", True)

    headers = [
        labels["subject"],
        labels["average"],
        labels["scale"],
        labels["coefficient"],
    ]
    if show_rank:
        headers.append(labels["rank"])
    if show_class_average:
        headers.append(labels["class_average"])
    if show_comments:
        headers.append(labels["comment"])

    body = []
    for subject in payload.get("subjects") or []:
        row = [
            escape(str(subject.get("subject_name") or "—")),
            _fmt(subject.get("average")),
            _fmt(subject.get("max_score")),
            _fmt(subject.get("coefficient")),
        ]
        if show_rank:
            row.append(_fmt(subject.get("rank")))
        if show_class_average:
            row.append(_fmt(subject.get("class_average")))
        if show_comments:
            row.append(escape(str(subject.get("appreciation") or "—")))
        body.append(row)

    return headers, body


def render_public_report_card_html(*, request, snapshot):
    payload = snapshot.payload or {}
    language = (payload.get("language") or {}).get("code") or "FR"
    labels = EN if language == "EN" else FR
    lang_attr = "en" if language == "EN" else "fr"

    school_payload = payload.get("school") or {}
    school = snapshot.school
    school_name = school_payload.get("name") or school.name
    acronym = school_payload.get("acronym") or school.acronym
    motto = school_payload.get("motto") or school.motto
    primary = _color(
        school_payload.get("primary_color") or school.primary_color,
        "#144dd2",
    )
    secondary = _color(
        school_payload.get("secondary_color") or school.secondary_color,
        "#0a0a0b",
    )
    logo_url = _school_logo_url(request, school)
    photo_url = _student_photo_url(request, snapshot, payload)

    student = payload.get("student") or {}
    academic = payload.get("academic") or {}
    summary = payload.get("summary") or {}
    comments = payload.get("comments") or {}
    template_options = ((payload.get("template") or {}).get("options") or {})
    fingerprint = snapshot.payload_sha256[:16].upper()

    headers, rows = _subject_rows(payload, labels)
    head_html = "".join(f"<th>{escape(str(item))}</th>" for item in headers)
    rows_html = ""
    for row in rows:
        rows_html += "<tr>" + "".join(f"<td>{item}</td>" for item in row) + "</tr>"
    if not rows:
        rows_html = (
            f'<tr><td class="empty" colspan="{max(len(headers), 1)}">'
            f'{escape(labels["no_subjects"])}</td></tr>'
        )

    logo_html = ""
    if logo_url:
        logo_html = (
            f'<img class="school-logo" src="{escape(logo_url, quote=True)}" '
            f'alt="{escape(str(school_name), quote=True)}">'
        )
    else:
        fallback = escape((acronym or school_name or "BW")[:4].upper())
        logo_html = f'<div class="school-logo logo-fallback">{fallback}</div>'

    photo_html = ""
    if photo_url:
        photo_html = (
            f'<img class="student-photo" src="{escape(photo_url, quote=True)}" '
            f'alt="{escape(str(student.get("name") or ""), quote=True)}">'
        )

    show_decision = template_options.get("show_decision", True)
    decision_html = ""
    if show_decision and summary.get("promotion_decision_label"):
        decision_html = f"""
        <div class="summary-card">
          <span>{escape(labels["decision"])}</span>
          <strong>{escape(str(summary.get("promotion_decision_label")))}</strong>
        </div>
        """

    teacher_comment_html = ""
    if template_options.get("show_teacher_comment", True) and comments.get("teacher"):
        teacher_comment_html = f"""
        <div class="comment-card">
          <div class="comment-title">{escape(labels["teacher_comment"])}</div>
          <div>{escape(str(comments.get("teacher")))}</div>
        </div>
        """

    management_comment_html = ""
    if template_options.get("show_direction_comment", True) and comments.get("general"):
        management_comment_html = f"""
        <div class="comment-card">
          <div class="comment-title">{escape(labels["management_comment"])}</div>
          <div>{escape(str(comments.get("general")))}</div>
        </div>
        """

    published_text = snapshot.published_at.strftime("%d/%m/%Y %H:%M")
    period_name = _period_name(payload, labels)
    student_name = student.get("name") or (
        f"{snapshot.enrollment.student.last_name} "
        f"{snapshot.enrollment.student.first_name}"
    ).strip()

    return f"""<!doctype html>
<html lang="{lang_attr}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="{primary}">
  <title>{escape(labels["page_title"])} - {escape(str(school_name))}</title>
  <style>
    :root {{
      --primary: {primary};
      --secondary: {secondary};
      --primary-soft: color-mix(in srgb, var(--primary) 10%, white);
      --primary-border: color-mix(in srgb, var(--primary) 22%, white);
      --text: #172033;
      --muted: #64748b;
      --surface: rgba(255,255,255,.94);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 8% 5%, color-mix(in srgb, var(--primary) 15%, transparent), transparent 32rem),
        radial-gradient(circle at 95% 8%, color-mix(in srgb, var(--secondary) 12%, transparent), transparent 30rem),
        #f7f9fd;
    }}
    .brand-strip {{
      height: 6px;
      background: linear-gradient(90deg, var(--primary), var(--secondary));
    }}
    .page {{
      width: min(1120px, calc(100% - 28px));
      margin: 0 auto;
      padding: 24px 0 46px;
    }}
    .school-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      border: 1px solid var(--primary-border);
      background: var(--surface);
      border-radius: 24px;
      padding: 18px 20px;
      box-shadow: 0 18px 55px rgba(15,23,42,.08);
    }}
    .school-id {{ display: flex; align-items: center; gap: 14px; min-width: 0; }}
    .school-logo {{
      width: 58px; height: 58px; flex: 0 0 auto;
      border-radius: 17px; object-fit: contain; background: #fff;
      border: 1px solid var(--primary-border); padding: 5px;
    }}
    .logo-fallback {{
      display: grid; place-items: center; padding: 0;
      color: white; background: var(--primary); font-weight: 800;
    }}
    .school-name {{ margin: 0; font-size: clamp(19px, 4vw, 28px); line-height: 1.1; }}
    .motto {{ margin-top: 5px; color: var(--muted); font-size: 13px; }}
    .verified {{
      display: inline-flex; align-items: center; gap: 7px;
      border-radius: 999px; padding: 9px 12px;
      background: #ecfdf5; color: #047857; font-size: 12px; font-weight: 800;
      white-space: nowrap;
    }}
    .hero {{
      margin-top: 18px;
      overflow: hidden;
      border: 1px solid var(--primary-border);
      border-radius: 26px;
      background:
        linear-gradient(135deg,
          color-mix(in srgb, var(--primary) 13%, white),
          color-mix(in srgb, var(--secondary) 7%, white),
          white);
    }}
    .hero-inner {{
      display: flex; align-items: center; gap: 18px; padding: 22px;
    }}
    .student-photo {{
      width: 94px; height: 106px; flex: 0 0 auto;
      object-fit: cover; border-radius: 20px; background: #fff;
      border: 4px solid white;
      box-shadow: 0 12px 30px color-mix(in srgb, var(--primary) 18%, transparent);
    }}
    .eyebrow {{
      color: var(--primary); font-size: 12px; font-weight: 800;
      letter-spacing: .13em; text-transform: uppercase;
    }}
    .student-name {{ margin: 5px 0 0; font-size: clamp(23px, 5vw, 34px); line-height: 1.08; }}
    .hero-sub {{ margin-top: 7px; color: var(--muted); }}
    .meta-grid {{
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 10px; margin-top: 16px;
    }}
    .meta, .summary-card, .comment-card {{
      border: 1px solid #e5eaf3; background: rgba(255,255,255,.88);
      border-radius: 17px; padding: 14px;
    }}
    .meta span, .summary-card span {{
      display: block; color: var(--muted); font-size: 11px; font-weight: 700;
      text-transform: uppercase; letter-spacing: .06em;
    }}
    .meta strong, .summary-card strong {{ display: block; margin-top: 6px; font-size: 15px; }}
    .section {{
      margin-top: 18px; border: 1px solid #e5eaf3;
      background: var(--surface); border-radius: 24px; padding: 20px;
      box-shadow: 0 14px 44px rgba(15,23,42,.055);
    }}
    .section-title {{ margin: 0 0 14px; font-size: 18px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid #e7ecf4; border-radius: 17px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
    th {{
      text-align: left; padding: 12px 13px;
      background: color-mix(in srgb, var(--primary) 7%, #f8fafc);
      color: #536079; font-size: 11px; text-transform: uppercase; letter-spacing: .045em;
    }}
    td {{ padding: 12px 13px; border-top: 1px solid #edf1f7; font-size: 13px; }}
    tbody tr:hover {{ background: color-mix(in srgb, var(--primary) 3%, white); }}
    .empty {{ color: var(--muted); text-align: center; padding: 24px; }}
    .summary-grid {{
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 10px; margin-top: 16px;
    }}
    .summary-card {{
      background: color-mix(in srgb, var(--primary) 5%, white);
      border-color: var(--primary-border);
    }}
    .summary-card strong {{ font-size: 19px; color: var(--primary); }}
    .comments {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }}
    .comment-title {{ color: var(--primary); font-size: 12px; font-weight: 800; margin-bottom: 7px; }}
    .verification {{
      display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: center;
      margin-top: 18px; padding: 17px 18px; border-radius: 20px;
      background: #111827; color: white;
    }}
    .verification small {{ color: #cbd5e1; }}
    .fingerprint {{ margin-top: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }}
    .print {{
      border: 0; border-radius: 13px; padding: 11px 15px;
      background: var(--primary); color: white; font-weight: 800; cursor: pointer;
    }}
    .footer {{ text-align: center; color: var(--muted); font-size: 12px; padding: 22px 10px 0; }}
    @media (max-width: 850px) {{
      .meta-grid, .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .comments {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 560px) {{
      .page {{ width: min(100% - 18px, 1120px); padding-top: 12px; }}
      .school-header {{ align-items: flex-start; padding: 15px; border-radius: 20px; }}
      .verified {{ padding: 7px 9px; font-size: 10px; }}
      .school-logo {{ width: 48px; height: 48px; border-radius: 14px; }}
      .hero-inner {{ padding: 17px; align-items: flex-start; }}
      .student-photo {{ width: 76px; height: 86px; border-radius: 17px; }}
      .meta-grid, .summary-grid {{ grid-template-columns: 1fr 1fr; }}
      .section {{ padding: 14px; border-radius: 20px; }}
      .verification {{ grid-template-columns: 1fr; }}
      .print {{ width: 100%; }}
    }}
    @media print {{
      body {{ background: white; }}
      .brand-strip, .print {{ display: none; }}
      .page {{ width: 100%; padding: 0; }}
      .school-header, .section {{ box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <div class="brand-strip"></div>
  <main class="page">
    <header class="school-header">
      <div class="school-id">
        {logo_html}
        <div>
          <h1 class="school-name">{escape(str(school_name))}</h1>
          {f'<div class="motto">{escape(str(motto))}</div>' if motto else ''}
        </div>
      </div>
      <div class="verified">✓ {escape(labels["verified"])}</div>
    </header>

    <section class="hero">
      <div class="hero-inner">
        {photo_html}
        <div>
          <div class="eyebrow">{escape(labels["official"])}</div>
          <h2 class="student-name">{escape(str(student_name))}</h2>
          <div class="hero-sub">{escape(period_name)} · {escape(str(payload.get("academic_year", {}).get("name") or snapshot.academic_year.name))}</div>
        </div>
      </div>
    </section>

    <div class="meta-grid">
      <div class="meta"><span>{escape(labels["student_id"])}</span><strong>{escape(str(student.get("matricule") or "—"))}</strong></div>
      <div class="meta"><span>{escape(labels["classroom"])}</span><strong>{escape(str(academic.get("classroom") or snapshot.enrollment.classroom.name))}</strong></div>
      <div class="meta"><span>{escape(labels["level"])}</span><strong>{escape(str(academic.get("level") or "—"))}</strong></div>
      <div class="meta"><span>{escape(labels["year"])}</span><strong>{escape(str(payload.get("academic_year", {}).get("name") or snapshot.academic_year.name))}</strong></div>
    </div>

    <section class="section">
      <h3 class="section-title">{escape(labels["page_title"])}</h3>
      <div class="table-wrap">
        <table>
          <thead><tr>{head_html}</tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>

      <div class="summary-grid">
        <div class="summary-card">
          <span>{escape(labels["overall"])}</span>
          <strong>{_fmt(summary.get("overall_average"))} / {_fmt(summary.get("default_scale"))}</strong>
        </div>
        <div class="summary-card">
          <span>{escape(labels["class_rank"])}</span>
          <strong>{_fmt(summary.get("rank"))}</strong>
        </div>
        <div class="summary-card">
          <span>{escape(labels["class_size"])}</span>
          <strong>{_fmt(summary.get("class_size"))}</strong>
        </div>
        {decision_html}
      </div>

      <div class="comments">
        {teacher_comment_html}
        {management_comment_html}
      </div>
    </section>

    <section class="verification">
      <div>
        <strong>{escape(labels["verification"])}</strong><br>
        <small>{escape(labels["secured"])}</small>
        <div class="fingerprint">{escape(labels["fingerprint"])}: {fingerprint} · {escape(labels["version"])} {snapshot.version} · {escape(labels["published"])} {published_text}</div>
      </div>
      <button class="print" type="button" onclick="window.print()">{escape(labels["print"])}</button>
    </section>

    <div class="footer">
      {escape(str(school_name))}
      {f' · {escape(str(school.city))}' if school.city else ''}
      {f' · {escape(str(school.phone))}' if school.phone else ''}
    </div>
  </main>
</body>
</html>"""
