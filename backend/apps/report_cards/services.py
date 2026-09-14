import hashlib
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership
from apps.academics.models import (
    AcademicPeriod,
    AcademicPolicy,
    AcademicYear,
    Classroom,
    Cycle,
    Section,
    LevelSubject,
    Subject,
)
from apps.assessments.services import (
    calculate_period_result,
    calculate_subject_average,
    calculate_year_average,
)
from apps.people.models import Enrollment
from apps.teaching.models import ClassroomLeadership, TeachingAssignment
from apps.teaching.services import get_teacher_profile_for_user

from .models import ReportCardSnapshot, ReportCardTemplate
from .pdf import generate_report_card_pdf


THREE = Decimal("0.001")

REPORT_LANGUAGE_FR = "FR"
REPORT_LANGUAGE_EN = "EN"


def _section_language_code(enrollment):
    section_language = enrollment.classroom.level.cycle.section.language
    if section_language == Section.Language.ENGLISH:
        return REPORT_LANGUAGE_EN
    if section_language == Section.Language.FRENCH:
        return REPORT_LANGUAGE_FR

    school_language = enrollment.school.language_mode
    if school_language == "ENGLISH":
        return REPORT_LANGUAGE_EN
    return REPORT_LANGUAGE_FR


def resolve_report_card_language(*, enrollment, template=None):
    """Resolve one immutable document language for this report card.

    AUTO follows the student's academic section. For an explicitly bilingual
    section, the school language is used when it is unambiguous; otherwise FR
    is the deterministic fallback. A template may explicitly force FR or EN.
    """
    mode = (
        template.language_mode
        if template is not None
        else ReportCardTemplate.LanguageMode.AUTO
    )

    if mode == ReportCardTemplate.LanguageMode.ENGLISH:
        return REPORT_LANGUAGE_EN
    if mode == ReportCardTemplate.LanguageMode.FRENCH:
        return REPORT_LANGUAGE_FR
    return _section_language_code(enrollment)


def report_language_payload(*, enrollment, template=None, code=None):
    code = code or resolve_report_card_language(
        enrollment=enrollment,
        template=template,
    )
    section_language = enrollment.classroom.level.cycle.section.language
    mode = (
        template.language_mode
        if template is not None
        else ReportCardTemplate.LanguageMode.AUTO
    )

    if mode != ReportCardTemplate.LanguageMode.AUTO:
        source = "TEMPLATE"
    elif section_language in {
        Section.Language.FRENCH,
        Section.Language.ENGLISH,
    }:
        source = "SECTION"
    elif enrollment.school.language_mode in {"FRENCH", "ENGLISH"}:
        source = "SCHOOL"
    else:
        source = "DEFAULT"

    return {
        "code": code,
        "label": "English" if code == REPORT_LANGUAGE_EN else "Français",
        "mode": mode,
        "source": source,
        "section_language": section_language,
    }


def q(value):
    if value is None:
        return None
    return Decimal(value).quantize(THREE, rounding=ROUND_HALF_UP)


def display_user(user):
    name = user.get_full_name().strip() if user else ""
    return name or (user.email if user else "")


def get_membership(request):
    return get_school_membership(request)


def is_manager(request):
    membership = get_membership(request)
    return bool(
        membership
        and membership.role
        in {
            SchoolMembership.Role.OWNER,
            SchoolMembership.Role.DIRECTOR,
            SchoolMembership.Role.MANAGER,
        }
    )


def teacher_full_report_class_ids(*, school, user):
    teacher = get_teacher_profile_for_user(user=user, school=school)
    if not teacher:
        return set()

    return set(
        ClassroomLeadership.objects.filter(
            school=school,
            teacher=teacher,
            is_active=True,
            role__in=[
                ClassroomLeadership.Role.CLASS_TEACHER,
                ClassroomLeadership.Role.HOMEROOM_TEACHER,
            ],
        ).values_list("classroom_id", flat=True)
    )


def teacher_subject_contexts(*, school, user):
    teacher = get_teacher_profile_for_user(user=user, school=school)
    if not teacher:
        return set()

    return set(
        TeachingAssignment.objects.filter(
            school=school,
            teacher=teacher,
            is_active=True,
        ).values_list("classroom_id", "subject_id")
    )


def can_view_full_class(*, request, classroom):
    if is_manager(request):
        return True

    return classroom.id in teacher_full_report_class_ids(
        school=request.school,
        user=request.user,
    )


def can_view_subject(*, request, classroom, subject):
    if is_manager(request):
        return True

    if can_view_full_class(request=request, classroom=classroom):
        return True

    return (
        classroom.id,
        subject.id,
    ) in teacher_subject_contexts(
        school=request.school,
        user=request.user,
    )


def build_options(*, request):
    school = request.school
    manager = is_manager(request)

    years = AcademicYear.objects.filter(
        school=school
    ).order_by("-start_date")

    if manager:
        classrooms = Classroom.objects.filter(
            school=school,
            is_active=True,
        ).select_related("academic_year", "level")
        full_ids = set(classrooms.values_list("id", flat=True))
        subject_ids = set(
            LevelSubject.objects.filter(
                school=school,
                is_active=True,
                subject__is_active=True,
            ).values_list("subject_id", flat=True)
        )
    else:
        full_ids = teacher_full_report_class_ids(
            school=school,
            user=request.user,
        )
        contexts = teacher_subject_contexts(
            school=school,
            user=request.user,
        )
        class_ids = full_ids | {item[0] for item in contexts}
        subject_ids = {item[1] for item in contexts}
        if full_ids:
            subject_ids |= set(
                LevelSubject.objects.filter(
                    school=school,
                    level__classrooms__id__in=full_ids,
                    is_active=True,
                    subject__is_active=True,
                ).values_list("subject_id", flat=True)
            )
        classrooms = Classroom.objects.filter(
            school=school,
            id__in=class_ids,
            is_active=True,
        ).select_related("academic_year", "level")

    year_ids = set(classrooms.values_list("academic_year_id", flat=True))
    years = years.filter(id__in=year_ids) if not manager else years

    periods = AcademicPeriod.objects.filter(
        school=school,
        academic_year_id__in=years.values_list("id", flat=True),
        is_active=True,
    ).select_related("academic_year").order_by(
        "-academic_year__start_date",
        "order",
    )

    subjects = Subject.objects.filter(
        school=school,
        id__in=subject_ids,
        is_active=True,
    ).order_by("name")

    classroom_subjects = {}
    for classroom in classrooms:
        allowed = set(
            LevelSubject.objects.filter(
                school=school,
                level=classroom.level,
                is_active=True,
                subject__is_active=True,
            ).values_list("subject_id", flat=True)
        )
        if not manager and classroom.id not in full_ids:
            allowed &= {
                subject_id
                for class_id, subject_id in contexts
                if class_id == classroom.id
            }
        classroom_subjects[str(classroom.id)] = sorted(allowed)

    return {
        "years": [
            {
                "id": item.id,
                "name": item.name,
                "is_active": item.is_active,
            }
            for item in years
        ],
        "periods": [
            {
                "id": item.id,
                "name": item.name,
                "academic_year": item.academic_year_id,
                "order": item.order,
            }
            for item in periods
        ],
        "classrooms": [
            {
                "id": item.id,
                "name": item.name,
                "academic_year": item.academic_year_id,
                "academic_year_name": item.academic_year.name,
                "level": item.level_id,
                "level_name": item.level.name,
            }
            for item in classrooms.order_by(
                "-academic_year__start_date",
                "level__order",
                "name",
            )
        ],
        "subjects": [
            {
                "id": item.id,
                "name": item.name,
            }
            for item in subjects
        ],
        "full_report_class_ids": sorted(full_ids),
        "classroom_subjects": classroom_subjects,
        "cycles": [
            {
                "id": item.id,
                "name": item.name,
                "section_name": item.section.name,
            }
            for item in Cycle.objects.filter(
                school=school,
                is_active=True,
            ).select_related("section").order_by(
                "section__order",
                "order",
                "name",
            )
        ],
    }


def dense_ranks(items, *, value_key):
    """
    Classement dense :
        15, 15, 13, 12  ->  1, 1, 2, 3

    Deux élèves peuvent donc être premiers ex æquo et le rang suivant
    est 2, comme demandé pour les bulletins BE WISE School.
    """
    sorted_items = sorted(
        [
            item
            for item in items
            if item.get(value_key) is not None
        ],
        key=lambda item: Decimal(str(item[value_key])),
        reverse=True,
    )

    rank_map = {}
    previous_value = None
    current_rank = 0

    for item in sorted_items:
        value = Decimal(str(item[value_key]))
        if previous_value is None or value != previous_value:
            current_rank += 1
            previous_value = value

        rank_map[item["enrollment_id"]] = current_rank

    return rank_map


def class_period_results(*, school, classroom, period):
    enrollments = list(
        Enrollment.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related("student", "classroom__level")
        .order_by("student__last_name", "student__first_name")
    )

    students = []
    for enrollment in enrollments:
        result = calculate_period_result(
            enrollment=enrollment,
            academic_period=period,
        )
        students.append({
            "enrollment_id": enrollment.id,
            "student_id": enrollment.student_id,
            "student_name": (
                f"{enrollment.student.last_name} "
                f"{enrollment.student.first_name}"
            ).strip(),
            "matricule": enrollment.student.matricule,
            "overall_average": result["overall_average"],
            "subjects": result["subjects"],
        })

    ranks = dense_ranks(
        students,
        value_key="overall_average",
    )

    for item in students:
        item["rank"] = ranks.get(item["enrollment_id"])

    students.sort(
        key=lambda item: (
            item["rank"] is None,
            item["rank"] or 999999,
            item["student_name"],
        )
    )

    return {
        "classroom_id": classroom.id,
        "classroom_name": classroom.name,
        "academic_year_id": classroom.academic_year_id,
        "academic_year_name": classroom.academic_year.name,
        "period_id": period.id,
        "period_name": period.name,
        "class_size": len(enrollments),
        "students": students,
    }


def subject_period_results(*, school, classroom, period, subject):
    enrollments = list(
        Enrollment.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related("student", "classroom__level")
        .order_by("student__last_name", "student__first_name")
    )

    rows = []
    for enrollment in enrollments:
        result = calculate_subject_average(
            enrollment=enrollment,
            academic_period=period,
            subject=subject,
        )
        rows.append({
            "enrollment_id": enrollment.id,
            "student_id": enrollment.student_id,
            "student_name": (
                f"{enrollment.student.last_name} "
                f"{enrollment.student.first_name}"
            ).strip(),
            "matricule": enrollment.student.matricule,
            "average": result["average"] if result else None,
            "max_score": result["max_score"] if result else None,
            "coefficient": result["coefficient"] if result else None,
            "assessment_count": result["assessment_count"] if result else 0,
        })

    ranks = dense_ranks(rows, value_key="average")
    values = [
        Decimal(str(item["average"]))
        for item in rows
        if item["average"] is not None
    ]
    class_average = q(sum(values) / len(values)) if values else None

    for item in rows:
        item["rank"] = ranks.get(item["enrollment_id"])
        item["class_average"] = class_average

    rows.sort(
        key=lambda item: (
            item["rank"] is None,
            item["rank"] or 999999,
            item["student_name"],
        )
    )

    return {
        "classroom_id": classroom.id,
        "classroom_name": classroom.name,
        "period_id": period.id,
        "period_name": period.name,
        "subject_id": subject.id,
        "subject_name": subject.name,
        "class_average": class_average,
        "highest": max(values) if values else None,
        "lowest": min(values) if values else None,
        "students": rows,
    }


def _subject_stats_for_period(*, school, classroom, period, subject_id):
    subject = Subject.objects.get(
        school=school,
        id=subject_id,
    )
    data = subject_period_results(
        school=school,
        classroom=classroom,
        period=period,
        subject=subject,
    )
    return {
        item["enrollment_id"]: item
        for item in data["students"]
    }


def student_period_result(*, school, enrollment, period):
    classroom_data = class_period_results(
        school=school,
        classroom=enrollment.classroom,
        period=period,
    )
    row = next(
        (
            item
            for item in classroom_data["students"]
            if item["enrollment_id"] == enrollment.id
        ),
        None,
    )
    if row is None:
        return None

    detailed_subjects = []
    for subject_row in row["subjects"]:
        stats = _subject_stats_for_period(
            school=school,
            classroom=enrollment.classroom,
            period=period,
            subject_id=subject_row["subject_id"],
        ).get(enrollment.id, {})

        detailed_subjects.append({
            **subject_row,
            "rank": stats.get("rank"),
            "class_average": stats.get("class_average"),
        })

    return {
        **row,
        "subjects": detailed_subjects,
        "classroom_id": enrollment.classroom_id,
        "classroom_name": enrollment.classroom.name,
        "level_name": enrollment.classroom.level.name,
        "academic_year_id": enrollment.academic_year_id,
        "academic_year_name": enrollment.academic_year.name,
        "period_id": period.id,
        "period_name": period.name,
        "class_size": classroom_data["class_size"],
    }


def _annual_subject_rows(*, enrollment):
    periods = list(
        enrollment.academic_year.periods.filter(
            is_active=True
        ).order_by("order")
    )

    configs = list(
        LevelSubject.objects.filter(
            school=enrollment.school,
            level=enrollment.classroom.level,
            is_active=True,
            subject__is_active=True,
        ).select_related("subject").order_by("order", "subject__name")
    )

    rows = []
    for config in configs:
        weighted_sum = Decimal("0")
        total_weight = Decimal("0")
        max_score = None

        for period in periods:
            result = calculate_subject_average(
                enrollment=enrollment,
                academic_period=period,
                subject=config.subject,
            )
            if not result:
                continue
            weight = Decimal(period.weight)
            weighted_sum += Decimal(result["average"]) * weight
            total_weight += weight
            max_score = result["max_score"]

        if total_weight == 0:
            continue

        rows.append({
            "subject_id": config.subject_id,
            "subject_name": config.subject.name,
            "average": q(weighted_sum / total_weight),
            "max_score": max_score,
            "coefficient": q(config.coefficient),
        })

    return rows


def class_annual_results(*, school, classroom):
    enrollments = list(
        Enrollment.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).select_related("student", "classroom__level")
    )

    students = []
    for enrollment in enrollments:
        annual_average, periods = calculate_year_average(
            enrollment=enrollment
        )
        students.append({
            "enrollment_id": enrollment.id,
            "student_id": enrollment.student_id,
            "student_name": (
                f"{enrollment.student.last_name} "
                f"{enrollment.student.first_name}"
            ).strip(),
            "matricule": enrollment.student.matricule,
            "overall_average": annual_average,
            "periods": periods,
        })

    ranks = dense_ranks(
        students,
        value_key="overall_average",
    )
    for item in students:
        item["rank"] = ranks.get(item["enrollment_id"])

    students.sort(
        key=lambda item: (
            item["rank"] is None,
            item["rank"] or 999999,
            item["student_name"],
        )
    )

    return {
        "classroom_id": classroom.id,
        "classroom_name": classroom.name,
        "academic_year_id": classroom.academic_year_id,
        "academic_year_name": classroom.academic_year.name,
        "class_size": len(students),
        "students": students,
    }


def student_annual_result(*, school, enrollment):
    class_data = class_annual_results(
        school=school,
        classroom=enrollment.classroom,
    )
    row = next(
        (
            item
            for item in class_data["students"]
            if item["enrollment_id"] == enrollment.id
        ),
        None,
    )
    if not row:
        return None

    return {
        **row,
        "subjects": _annual_subject_rows(enrollment=enrollment),
        "classroom_id": enrollment.classroom_id,
        "classroom_name": enrollment.classroom.name,
        "level_name": enrollment.classroom.level.name,
        "academic_year_id": enrollment.academic_year_id,
        "academic_year_name": enrollment.academic_year.name,
        "class_size": class_data["class_size"],
        "promotion_decision": enrollment.promotion_decision,
        "promotion_decision_label": promotion_decision_label(enrollment),
    }


def class_teacher_name(*, enrollment):
    leadership = (
        ClassroomLeadership.objects.filter(
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            classroom=enrollment.classroom,
            is_active=True,
            role__in=[
                ClassroomLeadership.Role.CLASS_TEACHER,
                ClassroomLeadership.Role.HOMEROOM_TEACHER,
            ],
        )
        .select_related("teacher")
        .order_by("role")
        .first()
    )
    if not leadership:
        return ""
    return (
        f"{leadership.teacher.last_name} "
        f"{leadership.teacher.first_name}"
    ).strip()


def auto_appreciation(average, max_score, language=REPORT_LANGUAGE_FR):
    if average is None or max_score in (None, 0):
        return ""

    ratio = Decimal(str(average)) / Decimal(str(max_score))
    english = language == REPORT_LANGUAGE_EN

    if ratio >= Decimal("0.90"):
        return "Excellent work." if english else "Excellent travail."
    if ratio >= Decimal("0.80"):
        return "Very good work." if english else "Très bon travail."
    if ratio >= Decimal("0.70"):
        return "Good work." if english else "Bon travail."
    if ratio >= Decimal("0.60"):
        return "Fairly good overall." if english else "Assez bon ensemble."
    if ratio >= Decimal("0.50"):
        return (
            "Satisfactory results; keep working."
            if english
            else "Résultats passables, efforts à poursuivre."
        )
    return (
        "Insufficient results; greater effort is expected."
        if english
        else "Résultats insuffisants, davantage d'efforts sont attendus."
    )


def auto_general_comment(average, max_score, language=REPORT_LANGUAGE_FR):
    if average is None:
        return (
            "Incomplete results for this period."
            if language == REPORT_LANGUAGE_EN
            else "Résultats incomplets pour cette période."
        )
    return auto_appreciation(average, max_score, language=language)


def promotion_decision_label(enrollment, language=None):
    """Return the end-of-year decision in the report-card language."""
    language = language or _section_language_code(enrollment)
    decision = enrollment.promotion_decision

    labels = {
        REPORT_LANGUAGE_FR: {
            Enrollment.PromotionDecision.PENDING:
                "Décision de fin d'année non arrêtée",
            Enrollment.PromotionDecision.PROMOTED: "Admis / promu",
            Enrollment.PromotionDecision.REPEATED: "Redouble",
            Enrollment.PromotionDecision.GRADUATED: "Diplômé",
            Enrollment.PromotionDecision.TRANSFERRED: "Transféré",
            Enrollment.PromotionDecision.WITHDRAWN: "Retiré",
        },
        REPORT_LANGUAGE_EN: {
            Enrollment.PromotionDecision.PENDING:
                "End-of-year decision pending",
            Enrollment.PromotionDecision.PROMOTED: "Promoted",
            Enrollment.PromotionDecision.REPEATED: "Repeat",
            Enrollment.PromotionDecision.GRADUATED: "Graduated",
            Enrollment.PromotionDecision.TRANSFERRED: "Transferred",
            Enrollment.PromotionDecision.WITHDRAWN: "Withdrawn",
        },
    }
    return labels.get(language, labels[REPORT_LANGUAGE_FR]).get(
        decision,
        enrollment.get_promotion_decision_display(),
    )


def _default_scale(school):
    policy, _ = AcademicPolicy.objects.get_or_create(school=school)
    return Decimal(policy.default_max_score)


def verification_url_for(snapshot):
    base = getattr(
        settings,
        "REPORT_CARD_VERIFY_BASE_URL",
        "",
    ).strip().rstrip("/")

    if base:
        return f"{base}/{snapshot.verification_token}/"

    scheme = "http" if settings.DEBUG else "https"
    host = (
        f"{snapshot.school.slug}.localhost:8000"
        if settings.DEBUG
        else f"{snapshot.school.slug}.{settings.BASE_DOMAIN}"
    )
    return (
        f"{scheme}://{host}/verify/report-card/"
        f"{snapshot.verification_token}/"
    )


def canonical_hash(payload):
    raw = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def report_content_payload(payload):
    """
    Returns only the meaningful report-card content.

    Metadata that necessarily changes on every publication attempt is excluded:
    version number, publication timestamp and verification token/fingerprint.

    Therefore clicking "Publish" twice without changing grades, comments,
    branding, class teacher, decision, etc. reuses the current snapshot.
    """
    content = json_safe(payload)
    content = json.loads(
        json.dumps(content, ensure_ascii=False)
    )

    content.pop("version", None)
    content.pop("published_at", None)
    content.pop("verification", None)
    content.pop("render", None)
    content.pop("preview", None)

    # Backward-compatible comparison with STEP 06.2 snapshots. Before 06.2.2
    # all generated PDFs were implicitly French and templates had no explicit
    # language_mode. Normalizing these defaults avoids creating an unnecessary
    # new version for an unchanged French bulletin immediately after upgrade.
    language = content.get("language")
    if isinstance(language, dict):
        content["language"] = language.get("code") or REPORT_LANGUAGE_FR
    elif not language:
        content["language"] = REPORT_LANGUAGE_FR

    template = content.get("template")
    if isinstance(template, dict):
        template.setdefault(
            "language_mode",
            ReportCardTemplate.LanguageMode.AUTO,
        )

    period = content.get("period")
    if isinstance(period, dict):
        # `kind` was added only to localize standard Term/Semester wording.
        # It is technical metadata and must not create a version by itself.
        period.pop("kind", None)

    return content


def report_content_hash(payload):
    return canonical_hash(report_content_payload(payload))


def _school_payload(school):
    return {
        "id": school.id,
        "slug": school.slug,
        "name": school.name,
        "acronym": school.acronym,
        "motto": school.motto,
        "city": school.city,
        "country": school.country,
        "phone": school.phone,
        "email": school.email,
        "primary_color": school.primary_color,
        "secondary_color": school.secondary_color,
    }



def fallback_template_payload():
    return {
        "id": None,
        "name": "Modèle classique",
        "key": ReportCardTemplate.TemplateKey.CLASSIC,
        "label": "Classique",
        "version": 1,
        "orientation": "PORTRAIT",
        "font_scale": "1.00",
        "language_mode": ReportCardTemplate.LanguageMode.AUTO,
        "scope": "SCHOOL",
        "cycle_id": None,
        "cycle_name": None,
        "options": {
            "show_rank": True,
            "show_class_average": True,
            "show_effective": True,
            "show_decision": True,
            "show_subject_comments": True,
            "show_teacher_comment": True,
            "show_direction_comment": True,
            "show_qr": True,
        },
    }


def template_to_payload(template):
    if template is None:
        return fallback_template_payload()

    return {
        "id": template.id,
        "name": template.name,
        "key": template.template_key,
        "label": template.get_template_key_display(),
        "version": template.version,
        "orientation": template.orientation,
        "font_scale": str(template.font_scale),
        "language_mode": template.language_mode,
        "scope": "CYCLE" if template.cycle_id else "SCHOOL",
        "cycle_id": template.cycle_id,
        "cycle_name": (
            template.cycle.name
            if template.cycle_id
            else None
        ),
        "options": {
            "show_rank": template.show_rank,
            "show_class_average": template.show_class_average,
            "show_effective": template.show_effective,
            "show_decision": template.show_decision,
            "show_subject_comments": template.show_subject_comments,
            "show_teacher_comment": template.show_teacher_comment,
            "show_direction_comment": template.show_direction_comment,
            "show_qr": template.show_qr,
        },
    }


def resolve_report_card_template(*, enrollment, template_id=None):
    queryset = ReportCardTemplate.objects.filter(
        school=enrollment.school,
    ).select_related("cycle")

    if template_id:
        return queryset.filter(id=template_id).first()

    cycle_id = enrollment.classroom.level.cycle_id

    template = (
        queryset.filter(
            cycle_id=cycle_id,
            is_default=True,
        )
        .order_by("-updated_at")
        .first()
    )
    if template:
        return template

    template = (
        queryset.filter(
            cycle__isnull=True,
            is_default=True,
        )
        .order_by("-updated_at")
        .first()
    )
    if template:
        return template

    template = (
        queryset.filter(cycle_id=cycle_id)
        .order_by("-updated_at")
        .first()
    )
    if template:
        return template

    return (
        queryset.filter(cycle__isnull=True)
        .order_by("-updated_at")
        .first()
    )


def attach_template_payload(
    *,
    payload,
    enrollment,
    template_id=None,
    template=None,
    document_language=None,
):
    if template is None:
        template = resolve_report_card_template(
            enrollment=enrollment,
            template_id=template_id,
        )
    if template_id and template is None:
        raise ValueError(
            "Le modèle de bulletin sélectionné est introuvable "
            "dans cet établissement."
        )

    document_language = document_language or resolve_report_card_language(
        enrollment=enrollment,
        template=template,
    )
    payload["template"] = template_to_payload(template)
    payload["language"] = report_language_payload(
        enrollment=enrollment,
        template=template,
        code=document_language,
    )
    return template


def preview_verification_url(enrollment):
    scheme = "http" if settings.DEBUG else "https"
    host = (
        f"{enrollment.school.slug}.localhost:8000"
        if settings.DEBUG
        else f"{enrollment.school.slug}.{settings.BASE_DOMAIN}"
    )
    return f"{scheme}://{host}/verify/report-card/preview-non-official/"


def build_preview_report_card(
    *,
    enrollment,
    report_type,
    publisher,
    academic_period=None,
    general_comment="",
    teacher_comment="",
    subject_comments=None,
    template_id=None,
):
    template = resolve_report_card_template(
        enrollment=enrollment,
        template_id=template_id,
    )
    if template_id and template is None:
        raise ValueError(
            "Le modèle de bulletin sélectionné est introuvable "
            "dans cet établissement."
        )
    document_language = resolve_report_card_language(
        enrollment=enrollment,
        template=template,
    )

    if report_type == ReportCardSnapshot.ReportType.PERIOD:
        payload = build_period_payload(
            enrollment=enrollment,
            period=academic_period,
            version=0,
            publisher=publisher,
            general_comment=general_comment,
            teacher_comment=teacher_comment,
            subject_comments=subject_comments,
            document_language=document_language,
        )
    else:
        payload = build_annual_payload(
            enrollment=enrollment,
            version=0,
            publisher=publisher,
            general_comment=general_comment,
            teacher_comment=teacher_comment,
            subject_comments=subject_comments,
            document_language=document_language,
        )

    attach_template_payload(
        payload=payload,
        enrollment=enrollment,
        template_id=template_id,
        template=template,
        document_language=document_language,
    )

    payload["preview"] = True
    payload["verification"] = {
        "url": preview_verification_url(enrollment),
        "fingerprint": (
            "PREVIEW"
            if document_language == REPORT_LANGUAGE_EN
            else "APERÇU"
        ),
    }
    payload = json_safe(payload)

    logo_path = None
    try:
        if enrollment.school.logo:
            logo_path = enrollment.school.logo.path
    except Exception:
        logo_path = None

    render = generate_report_card_pdf(
        payload=payload,
        verification_url=payload["verification"]["url"],
        logo_path=logo_path,
        return_meta=True,
    )

    return payload, render


def build_period_payload(
    *,
    enrollment,
    period,
    version,
    publisher,
    general_comment="",
    teacher_comment="",
    subject_comments=None,
    document_language=None,
):
    document_language = document_language or _section_language_code(enrollment)
    subject_comments = subject_comments or {}
    result = student_period_result(
        school=enrollment.school,
        enrollment=enrollment,
        period=period,
    )
    if not result or not result["subjects"]:
        raise ValueError(
            "Aucun résultat publié n'est disponible pour cet élève et cette période."
        )

    default_scale = _default_scale(enrollment.school)
    subjects = []
    for row in result["subjects"]:
        comment = (
            subject_comments.get(str(row["subject_id"]))
            or subject_comments.get(row["subject_id"])
            or auto_appreciation(
                row["average"],
                row["max_score"],
                language=document_language,
            )
        )
        subjects.append({
            **row,
            "appreciation": comment,
        })

    teacher_name = class_teacher_name(enrollment=enrollment)

    payload = {
        "schema_version": 1,
        "report_type": ReportCardSnapshot.ReportType.PERIOD,
        "version": version,
        "school": _school_payload(enrollment.school),
        "academic_year": {
            "id": enrollment.academic_year_id,
            "name": enrollment.academic_year.name,
        },
        "period": {
            "id": period.id,
            "name": period.name,
            "order": period.order,
            "kind": period.kind,
        },
        "student": {
            "id": enrollment.student_id,
            "name": (
                f"{enrollment.student.last_name} "
                f"{enrollment.student.first_name}"
            ).strip(),
            "matricule": enrollment.student.matricule,
            "gender": enrollment.student.gender,
        },
        "academic": {
            "classroom_id": enrollment.classroom_id,
            "classroom": enrollment.classroom.name,
            "level": enrollment.classroom.level.name,
            "cycle": enrollment.classroom.level.cycle.name,
            "section": enrollment.classroom.level.cycle.section.name,
            "class_teacher": teacher_name,
        },
        "subjects": subjects,
        "summary": {
            "overall_average": result["overall_average"],
            "rank": result["rank"],
            "class_size": result["class_size"],
            "default_scale": q(default_scale),
            "promotion_decision": enrollment.promotion_decision,
            "promotion_decision_label": promotion_decision_label(
                enrollment,
                language=document_language,
            ),
        },
        "attendance": {
            "absences": None,
            "late_arrivals": None,
        },
        "comments": {
            "teacher": (
                teacher_comment
                or auto_general_comment(
                    result["overall_average"],
                    default_scale,
                    language=document_language,
                )
            ),
            "general": general_comment,
        },
        "signatures": {
            "class_teacher": teacher_name,
            "publisher": display_user(publisher),
        },
        "published_at": timezone.now().isoformat(),
        "verification": {},
    }
    return payload


def build_annual_payload(
    *,
    enrollment,
    version,
    publisher,
    general_comment="",
    teacher_comment="",
    subject_comments=None,
    document_language=None,
):
    document_language = document_language or _section_language_code(enrollment)
    subject_comments = subject_comments or {}
    result = student_annual_result(
        school=enrollment.school,
        enrollment=enrollment,
    )
    if not result or result["overall_average"] is None:
        raise ValueError(
            "Aucune moyenne annuelle calculable n'est disponible pour cet élève."
        )

    default_scale = _default_scale(enrollment.school)
    subjects = []
    for row in result["subjects"]:
        comment = (
            subject_comments.get(str(row["subject_id"]))
            or subject_comments.get(row["subject_id"])
            or auto_appreciation(
                row["average"],
                row["max_score"],
                language=document_language,
            )
        )
        subjects.append({
            **row,
            "appreciation": comment,
        })

    teacher_name = class_teacher_name(enrollment=enrollment)

    payload = {
        "schema_version": 1,
        "report_type": ReportCardSnapshot.ReportType.ANNUAL,
        "version": version,
        "school": _school_payload(enrollment.school),
        "academic_year": {
            "id": enrollment.academic_year_id,
            "name": enrollment.academic_year.name,
        },
        "period": None,
        "student": {
            "id": enrollment.student_id,
            "name": (
                f"{enrollment.student.last_name} "
                f"{enrollment.student.first_name}"
            ).strip(),
            "matricule": enrollment.student.matricule,
            "gender": enrollment.student.gender,
        },
        "academic": {
            "classroom_id": enrollment.classroom_id,
            "classroom": enrollment.classroom.name,
            "level": enrollment.classroom.level.name,
            "cycle": enrollment.classroom.level.cycle.name,
            "section": enrollment.classroom.level.cycle.section.name,
            "class_teacher": teacher_name,
        },
        "subjects": subjects,
        "periods": result["periods"],
        "summary": {
            "overall_average": result["overall_average"],
            "rank": result["rank"],
            "class_size": result["class_size"],
            "default_scale": q(default_scale),
            "promotion_decision": result["promotion_decision"],
            "promotion_decision_label": promotion_decision_label(
                enrollment,
                language=document_language,
            ),
        },
        "attendance": {
            "absences": None,
            "late_arrivals": None,
        },
        "comments": {
            "teacher": (
                teacher_comment
                or auto_general_comment(
                    result["overall_average"],
                    default_scale,
                    language=document_language,
                )
            ),
            "general": general_comment,
        },
        "signatures": {
            "class_teacher": teacher_name,
            "publisher": display_user(publisher),
        },
        "published_at": timezone.now().isoformat(),
        "verification": {},
    }
    return payload


@transaction.atomic
def publish_report_card(
    *,
    enrollment,
    report_type,
    publisher,
    academic_period=None,
    general_comment="",
    teacher_comment="",
    subject_comments=None,
):
    queryset = ReportCardSnapshot.objects.select_for_update().filter(
        school=enrollment.school,
        enrollment=enrollment,
        report_type=report_type,
    )

    if report_type == ReportCardSnapshot.ReportType.PERIOD:
        queryset = queryset.filter(academic_period=academic_period)
    else:
        queryset = queryset.filter(academic_year=enrollment.academic_year)

    previous = queryset.order_by("-version").first()
    version = (previous.version + 1) if previous else 1

    template = resolve_report_card_template(enrollment=enrollment)
    document_language = resolve_report_card_language(
        enrollment=enrollment,
        template=template,
    )

    if report_type == ReportCardSnapshot.ReportType.PERIOD:
        payload = build_period_payload(
            enrollment=enrollment,
            period=academic_period,
            version=version,
            publisher=publisher,
            general_comment=general_comment,
            teacher_comment=teacher_comment,
            subject_comments=subject_comments,
            document_language=document_language,
        )
    else:
        payload = build_annual_payload(
            enrollment=enrollment,
            version=version,
            publisher=publisher,
            general_comment=general_comment,
            teacher_comment=teacher_comment,
            subject_comments=subject_comments,
            document_language=document_language,
        )

    attach_template_payload(
        payload=payload,
        enrollment=enrollment,
        template=template,
        document_language=document_language,
    )

    # No-op publication: keep the existing official version when the
    # meaningful content is strictly identical.
    if (
        previous
        and report_content_hash(previous.payload)
        == report_content_hash(payload)
    ):
        return previous, False

    snapshot = ReportCardSnapshot(
        school=enrollment.school,
        enrollment=enrollment,
        academic_year=enrollment.academic_year,
        academic_period=(
            academic_period
            if report_type == ReportCardSnapshot.ReportType.PERIOD
            else None
        ),
        report_type=report_type,
        version=version,
        supersedes=previous,
        payload={},
        payload_sha256="",
        pdf_sha256="",
        published_by=publisher,
    )

    # Le token est déjà fourni par le default au moment de l'instanciation
    # uniquement après field.get_default lors de save; on le force ici pour
    # construire l'URL avant le premier INSERT.
    if not snapshot.verification_token:
        from .models import generate_verification_token
        snapshot.verification_token = generate_verification_token()

    verification_url = verification_url_for(snapshot)
    payload["verification"] = {
        "url": verification_url,
        "fingerprint": "",
    }

    payload_hash = canonical_hash(payload)
    payload["verification"]["fingerprint"] = payload_hash[:16].upper()
    payload = json_safe(payload)
    payload_hash = canonical_hash(payload)

    logo_path = None
    try:
        if enrollment.school.logo:
            logo_path = enrollment.school.logo.path
    except Exception:
        logo_path = None

    render = generate_report_card_pdf(
        payload=payload,
        verification_url=verification_url,
        logo_path=logo_path,
        return_meta=True,
    )

    if not render["fits_one_page"]:
        template_name = payload.get("template", {}).get(
            "name",
            "modèle sélectionné",
        )
        raise ValueError(
            "Le bulletin ne tient pas sur une seule page A4 avec "
            f"« {template_name} ». Essayez le modèle Compact, le modèle "
            "Secondaire paysage, masquez certaines colonnes ou réduisez "
            "l'échelle de police."
        )

    payload["render"] = {
        "page_count": render["page_count"],
        "fits_one_page": True,
        "effective_font_scale": render["scale"],
        "emergency_compact": render["emergency_compact"],
        "orientation": render["orientation"],
    }
    payload = json_safe(payload)
    payload_hash = canonical_hash(payload)

    pdf_bytes = render["pdf_bytes"]
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    snapshot.payload = payload
    snapshot.payload_sha256 = payload_hash
    snapshot.pdf_sha256 = pdf_hash

    scope = (
        f"period-{academic_period.id}"
        if academic_period
        else "annual"
    )
    filename_prefix = (
        "report-card"
        if document_language == REPORT_LANGUAGE_EN
        else "bulletin"
    )
    filename = (
        f"{filename_prefix}-{enrollment.student.matricule}-"
        f"{scope}-v{version}.pdf"
    )
    snapshot.pdf_file.save(
        filename,
        ContentFile(pdf_bytes),
        save=False,
    )
    snapshot.save()

    return snapshot, True


def latest_snapshots(queryset):
    """
    Retourne seulement la dernière version de chaque bulletin logique.

    Utilisé côté UI lorsqu'on veut une vue simple des bulletins courants.
    L'historique complet reste disponible avec `latest_only=false`.
    """
    items = list(queryset)
    latest = {}
    for item in items:
        key = (
            item.enrollment_id,
            item.report_type,
            item.academic_period_id,
            item.academic_year_id,
        )
        if key not in latest or item.version > latest[key].version:
            latest[key] = item
    return sorted(
        latest.values(),
        key=lambda item: item.published_at,
        reverse=True,
    )
