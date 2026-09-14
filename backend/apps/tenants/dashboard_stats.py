from datetime import date
from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.accounts.models import SchoolMembership
from apps.academics.models import (
    AcademicPeriod,
    AcademicYear,
    Classroom,
    LevelSubject,
)
from apps.assessments.models import Assessment, Grade
from apps.finance.models import StudentTuitionAccount, TuitionPayment
from apps.finance.services import dashboard_summary as finance_dashboard_summary
from apps.people.models import Enrollment, Student, Teacher
from apps.report_cards.models import ReportCardSnapshot
from apps.teaching.models import ClassroomLeadership, TeachingAssignment


FINANCE_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
    SchoolMembership.Role.ACCOUNTANT,
}

ACADEMIC_ROLES = {
    SchoolMembership.Role.OWNER,
    SchoolMembership.Role.DIRECTOR,
    SchoolMembership.Role.MANAGER,
    SchoolMembership.Role.TEACHER,
}


def _month_start(value):
    return date(value.year, value.month, 1)


def _shift_month(value, delta):
    index = value.year * 12 + value.month - 1 + delta
    return date(index // 12, index % 12 + 1, 1)


def _percent(value, total):
    if not total:
        return 0.0
    return round((value / total) * 100, 1)


def _money(value):
    return str((value or Decimal("0")).quantize(Decimal("0.01")))


def _year_progress(academic_year):
    if not academic_year:
        return 0.0

    today = timezone.localdate()
    start = academic_year.start_date
    end = academic_year.end_date

    if today <= start:
        return 0.0
    if today >= end:
        return 100.0

    total_days = max((end - start).days, 1)
    elapsed = (today - start).days
    return round((elapsed / total_days) * 100, 1)


def _active_period(academic_year):
    if not academic_year:
        return None

    today = timezone.localdate()
    periods = AcademicPeriod.objects.filter(
        academic_year=academic_year,
        is_active=True,
    ).order_by("order", "name")

    current = (
        periods.filter(
            start_date__isnull=False,
            end_date__isnull=False,
            start_date__lte=today,
            end_date__gte=today,
        )
        .order_by("order")
        .first()
    )

    if current is None:
        current = periods.first()

    if current is None:
        return None

    return {
        "id": current.id,
        "name": current.name,
        "kind": current.kind,
        "order": current.order,
        "start_date": current.start_date,
        "end_date": current.end_date,
    }


def _teacher_scope(*, school, academic_year, user):
    teacher = (
        Teacher.objects.filter(
            school=school,
            user=user,
            status=Teacher.Status.ACTIVE,
        )
        .order_by("id")
        .first()
    )

    if not teacher or not academic_year:
        return {
            "teacher": teacher,
            "classroom_ids": [],
            "assignment_ids": [],
            "assignments_count": 0,
            "classes_count": 0,
        }

    assignments = TeachingAssignment.objects.filter(
        school=school,
        academic_year=academic_year,
        teacher=teacher,
        is_active=True,
    )
    leaderships = ClassroomLeadership.objects.filter(
        school=school,
        academic_year=academic_year,
        teacher=teacher,
        is_active=True,
    )

    assignment_classrooms = set(
        assignments.values_list("classroom_id", flat=True)
    )
    leadership_classrooms = set(
        leaderships.values_list("classroom_id", flat=True)
    )
    classroom_ids = sorted(
        assignment_classrooms | leadership_classrooms
    )

    return {
        "teacher": teacher,
        "classroom_ids": classroom_ids,
        "assignment_ids": list(
            assignments.values_list("id", flat=True)
        ),
        "assignments_count": assignments.count(),
        "classes_count": len(classroom_ids),
    }


def _population_stats(
    *,
    school,
    academic_year,
    classroom_ids=None,
):
    if not academic_year:
        return {
            "enrollments": 0,
            "gender": [],
            "cycles": [],
            "classrooms": [],
        }

    enrollments = Enrollment.objects.filter(
        school=school,
        academic_year=academic_year,
        status=Enrollment.Status.ACTIVE,
    )

    classrooms = Classroom.objects.filter(
        school=school,
        academic_year=academic_year,
        is_active=True,
    ).select_related(
        "level__cycle__section",
    )

    if classroom_ids is not None:
        enrollments = enrollments.filter(
            classroom_id__in=classroom_ids
        )
        classrooms = classrooms.filter(id__in=classroom_ids)

    enrollment_count = enrollments.count()

    raw_gender = {
        item["student__gender"] or "UNKNOWN": item["count"]
        for item in enrollments.values("student__gender")
        .annotate(count=Count("id"))
        .order_by()
    }

    gender_order = [
        Student.Gender.MALE,
        Student.Gender.FEMALE,
        Student.Gender.OTHER,
        "UNKNOWN",
    ]
    gender = [
        {
            "key": key,
            "count": raw_gender.get(key, 0),
            "percentage": _percent(
                raw_gender.get(key, 0),
                enrollment_count,
            ),
        }
        for key in gender_order
        if raw_gender.get(key, 0)
    ]

    cycles = list(
        enrollments.values(
            "classroom__level__cycle_id",
            "classroom__level__cycle__name",
            "classroom__level__cycle__kind",
            "classroom__level__cycle__section__name",
            "classroom__level__cycle__section__language",
            "classroom__level__cycle__section__order",
            "classroom__level__cycle__order",
        )
        .annotate(count=Count("id"))
        .order_by(
            "classroom__level__cycle__section__order",
            "classroom__level__cycle__order",
            "classroom__level__cycle__name",
        )
    )

    cycles = [
        {
            "id": row["classroom__level__cycle_id"],
            "name": row["classroom__level__cycle__name"],
            "kind": row["classroom__level__cycle__kind"],
            "section_name": (
                row["classroom__level__cycle__section__name"]
            ),
            "section_language": (
                row[
                    "classroom__level__cycle__section__language"
                ]
            ),
            "count": row["count"],
            "percentage": _percent(
                row["count"],
                enrollment_count,
            ),
        }
        for row in cycles
    ]

    classroom_counts = {
        row["classroom_id"]: row["count"]
        for row in enrollments.values("classroom_id")
        .annotate(count=Count("id"))
        .order_by()
    }

    classroom_rows = []
    for classroom in classrooms:
        count = classroom_counts.get(classroom.id, 0)
        capacity = classroom.capacity
        occupancy = (
            _percent(count, capacity)
            if capacity
            else None
        )
        classroom_rows.append({
            "id": classroom.id,
            "name": classroom.name,
            "level_name": classroom.level.name,
            "cycle_name": classroom.level.cycle.name,
            "section_name": classroom.level.cycle.section.name,
            "count": count,
            "capacity": capacity,
            "occupancy_rate": occupancy,
        })

    classroom_rows.sort(
        key=lambda item: (
            -item["count"],
            item["name"].lower(),
        )
    )

    return {
        "enrollments": enrollment_count,
        "gender": gender,
        "cycles": cycles,
        "classrooms": classroom_rows,
    }


def _assessment_stats(
    *,
    school,
    academic_year,
    teacher_scope=None,
):
    if not academic_year:
        return None

    assessments = Assessment.objects.filter(
        school=school,
        teaching_assignment__academic_year=academic_year,
    )

    if teacher_scope is not None:
        assessments = assessments.filter(
            teaching_assignment_id__in=teacher_scope[
                "assignment_ids"
            ]
        )

    status_counts = {
        row["status"]: row["count"]
        for row in assessments.values("status")
        .annotate(count=Count("id"))
        .order_by()
    }

    total = sum(status_counts.values())
    published = status_counts.get(
        Assessment.Status.PUBLISHED,
        0,
    )

    report_cards = ReportCardSnapshot.objects.filter(
        school=school,
        academic_year=academic_year,
    )

    if teacher_scope is not None:
        report_cards = report_cards.filter(
            enrollment__classroom_id__in=teacher_scope[
                "classroom_ids"
            ]
        )

    period_reports = (
        report_cards.filter(
            report_type=ReportCardSnapshot.ReportType.PERIOD
        )
        .values("enrollment_id", "academic_period_id")
        .distinct()
        .count()
    )
    annual_reports = (
        report_cards.filter(
            report_type=ReportCardSnapshot.ReportType.ANNUAL
        )
        .values("enrollment_id")
        .distinct()
        .count()
    )

    enrollment_scope = Enrollment.objects.filter(
        school=school,
        academic_year=academic_year,
    )
    if teacher_scope is not None:
        enrollment_scope = enrollment_scope.filter(
            classroom_id__in=teacher_scope["classroom_ids"]
        )

    average = (
        enrollment_scope.filter(final_average__isnull=False)
        .aggregate(value=Avg("final_average"))
        .get("value")
    )

    decisions = {
        row["promotion_decision"]: row["count"]
        for row in enrollment_scope.values("promotion_decision")
        .annotate(count=Count("id"))
        .order_by()
    }

    return {
        "assessments_total": total,
        "published_assessments": published,
        "publication_rate": _percent(published, total),
        "statuses": [
            {
                "key": status,
                "count": status_counts.get(status, 0),
                "percentage": _percent(
                    status_counts.get(status, 0),
                    total,
                ),
            }
            for status in [
                Assessment.Status.DRAFT,
                Assessment.Status.INPUT,
                Assessment.Status.SUBMITTED,
                Assessment.Status.VALIDATED,
                Assessment.Status.PUBLISHED,
            ]
        ],
        "published_report_cards": (
            period_reports + annual_reports
        ),
        "period_report_cards": period_reports,
        "annual_report_cards": annual_reports,
        "annual_average": (
            round(float(average), 2)
            if average is not None
            else None
        ),
        "promotion_decisions": [
            {
                "key": key,
                "count": decisions.get(key, 0),
            }
            for key in [
                Enrollment.PromotionDecision.PENDING,
                Enrollment.PromotionDecision.PROMOTED,
                Enrollment.PromotionDecision.REPEATED,
                Enrollment.PromotionDecision.GRADUATED,
                Enrollment.PromotionDecision.TRANSFERRED,
                Enrollment.PromotionDecision.WITHDRAWN,
            ]
            if decisions.get(key, 0)
        ],
    }


def _finance_stats(*, school, academic_year):
    if not academic_year:
        return None

    summary = finance_dashboard_summary(
        school=school,
        academic_year_id=academic_year.id,
    )

    payments = TuitionPayment.objects.filter(
        school=school,
        tuition_account__enrollment__academic_year=academic_year,
    )

    today = timezone.localdate()
    current_month = _month_start(today)
    month_total = (
        payments.filter(
            paid_at__year=today.year,
            paid_at__month=today.month,
        )
        .aggregate(total=Sum("amount"))
        .get("total")
        or Decimal("0")
    )

    first_month = _shift_month(current_month, -5)
    raw_months = (
        payments.filter(paid_at__date__gte=first_month)
        .annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    totals = {
        _month_start(item["month"].date()): item["total"]
        for item in raw_months
    }

    monthly_collections = []
    for offset in range(6):
        month = _shift_month(first_month, offset)
        monthly_collections.append({
            "year": month.year,
            "month": month.month,
            "amount": _money(
                totals.get(month, Decimal("0"))
            ),
        })

    currency = (
        StudentTuitionAccount.objects.filter(
            school=school,
            enrollment__academic_year=academic_year,
        )
        .values_list("plan__currency", flat=True)
        .first()
        or "XAF"
    )

    return {
        "currency": currency,
        "expected_total": _money(summary["expected_total"]),
        "collected_total": _money(summary["collected_total"]),
        "outstanding_total": _money(
            summary["outstanding_total"]
        ),
        "collection_rate": float(summary["collection_rate"]),
        "accounts_count": summary["accounts_count"],
        "paid_count": summary["paid_count"],
        "partial_count": summary["partial_count"],
        "unpaid_count": summary["unpaid_count"],
        "payments_today": _money(summary["payments_today"]),
        "payments_this_month": _money(month_total),
        "monthly_collections": monthly_collections,
    }


def build_dashboard_analytics(*, school, membership, user):
    active_year = (
        AcademicYear.objects.filter(
            school=school,
            is_active=True,
        )
        .order_by("-start_date")
        .first()
    )

    if active_year is None:
        active_year = (
            AcademicYear.objects.filter(school=school)
            .order_by("-start_date")
            .first()
        )

    is_teacher = (
        membership.role == SchoolMembership.Role.TEACHER
    )

    teacher_scope = (
        _teacher_scope(
            school=school,
            academic_year=active_year,
            user=user,
        )
        if is_teacher
        else None
    )

    population = _population_stats(
        school=school,
        academic_year=active_year,
        classroom_ids=(
            teacher_scope["classroom_ids"]
            if teacher_scope is not None
            else None
        ),
    )

    if active_year:
        active_classrooms = Classroom.objects.filter(
            school=school,
            academic_year=active_year,
            is_active=True,
        )
        if teacher_scope is not None:
            active_classrooms = active_classrooms.filter(
                id__in=teacher_scope["classroom_ids"]
            )
        classroom_count = active_classrooms.count()
    else:
        classroom_count = 0

    academics = None
    if membership.role in ACADEMIC_ROLES:
        academics = _assessment_stats(
            school=school,
            academic_year=active_year,
            teacher_scope=teacher_scope,
        )

    finance = None
    if membership.role in FINANCE_ROLES:
        finance = _finance_stats(
            school=school,
            academic_year=active_year,
        )

    teacher = None
    if teacher_scope is not None:
        teacher = {
            "profile_id": (
                teacher_scope["teacher"].id
                if teacher_scope["teacher"]
                else None
            ),
            "assignments_count": teacher_scope[
                "assignments_count"
            ],
            "classes_count": teacher_scope["classes_count"],
            "students_count": population["enrollments"],
        }

    return {
        "scope": "TEACHER" if is_teacher else "SCHOOL",
        "academic_year": (
            {
                "id": active_year.id,
                "name": active_year.name,
                "start_date": active_year.start_date,
                "end_date": active_year.end_date,
                "period_system": active_year.period_system,
                "is_active": active_year.is_active,
                "progress": _year_progress(active_year),
            }
            if active_year
            else None
        ),
        "active_period": _active_period(active_year),
        "overview": {
            "students": population["enrollments"],
            "classes": classroom_count,
            "teachers": school.teachers.filter(
                status=Teacher.Status.ACTIVE
            ).count(),
            "members": SchoolMembership.objects.filter(
                school=school,
                is_active=True,
            ).count(),
        },
        "population": population,
        "academics": academics,
        "finance": finance,
        "teacher": teacher,
        "generated_at": timezone.now(),
    }

def _classroom_teacher_scope_allowed(*, school, classroom, user):
    teacher = (
        Teacher.objects.filter(
            school=school,
            user=user,
            status=Teacher.Status.ACTIVE,
        )
        .order_by("id")
        .first()
    )
    if not teacher:
        return False

    return (
        TeachingAssignment.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            teacher=teacher,
            is_active=True,
        ).exists()
        or ClassroomLeadership.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            teacher=teacher,
            is_active=True,
        ).exists()
    )


def _classroom_gender_stats(*, school, classroom):
    enrollments = Enrollment.objects.filter(
        school=school,
        classroom=classroom,
        academic_year=classroom.academic_year,
        status=Enrollment.Status.ACTIVE,
    )
    total = enrollments.count()

    raw = {
        item["student__gender"] or "UNKNOWN": item["count"]
        for item in enrollments.values("student__gender")
        .annotate(count=Count("id"))
        .order_by()
    }

    order = [
        Student.Gender.MALE,
        Student.Gender.FEMALE,
        Student.Gender.OTHER,
        "UNKNOWN",
    ]
    rows = []
    for key in order:
        count = raw.get(key, 0)
        if not count:
            continue
        rows.append({
            "key": key,
            "count": count,
            "percentage": _percent(count, total),
        })

    return total, rows


def _classroom_teaching_stats(*, school, classroom):
    assignments = (
        TeachingAssignment.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            is_active=True,
        )
        .select_related("teacher", "subject")
        .order_by(
            "teacher__last_name",
            "teacher__first_name",
            "subject__name",
        )
    )

    leaderships = (
        ClassroomLeadership.objects.filter(
            school=school,
            academic_year=classroom.academic_year,
            classroom=classroom,
            is_active=True,
        )
        .select_related("teacher")
        .order_by("role", "teacher__last_name")
    )

    teachers = {}
    subjects = {
        level_subject.subject_id: {
            "id": level_subject.subject_id,
            "name": level_subject.subject.name,
        }
        for level_subject in LevelSubject.objects.filter(
            school=school,
            level=classroom.level,
            is_active=True,
        ).select_related("subject")
    }

    for assignment in assignments:
        teacher = assignment.teacher
        teacher_row = teachers.setdefault(
            teacher.id,
            {
                "id": teacher.id,
                "name": (
                    f"{teacher.last_name} {teacher.first_name}"
                ).strip(),
                "employee_number": teacher.employee_number,
                "subjects": [],
                "leadership_roles": [],
            },
        )
        teacher_row["subjects"].append({
            "id": assignment.subject_id,
            "name": assignment.subject.name,
        })
        subjects[assignment.subject_id] = {
            "id": assignment.subject_id,
            "name": assignment.subject.name,
        }

    for leadership in leaderships:
        teacher = leadership.teacher
        teacher_row = teachers.setdefault(
            teacher.id,
            {
                "id": teacher.id,
                "name": (
                    f"{teacher.last_name} {teacher.first_name}"
                ).strip(),
                "employee_number": teacher.employee_number,
                "subjects": [],
                "leadership_roles": [],
            },
        )
        teacher_row["leadership_roles"].append({
            "key": leadership.role,
            "label": leadership.get_role_display(),
        })

    return {
        "teachers_count": len(teachers),
        "subjects_count": len(subjects),
        "teachers": list(teachers.values()),
        "subjects": list(subjects.values()),
    }


def _classroom_subject_performance(
    *,
    school,
    classroom,
    active_period=None,
):
    grades = (
        Grade.objects.filter(
            school=school,
            enrollment__school=school,
            enrollment__classroom=classroom,
            enrollment__academic_year=classroom.academic_year,
            assessment__school=school,
            assessment__teaching_assignment__classroom=classroom,
            assessment__teaching_assignment__academic_year=(
                classroom.academic_year
            ),
            assessment__status=Assessment.Status.PUBLISHED,
            score__isnull=False,
            is_absent=False,
            is_exempt=False,
        )
        .select_related(
            "assessment",
            "assessment__teaching_assignment__subject",
        )
        .order_by()
    )

    if active_period:
        grades = grades.filter(
            assessment__academic_period_id=active_period["id"]
        )

    buckets = {}
    for grade in grades:
        assessment = grade.assessment
        max_score = assessment.max_score
        if not max_score:
            continue

        subject = assessment.teaching_assignment.subject
        item = buckets.setdefault(
            subject.id,
            {
                "id": subject.id,
                "name": subject.name,
                "sum": Decimal("0"),
                "count": 0,
            },
        )
        normalized = (
            Decimal(grade.score)
            / Decimal(max_score)
            * Decimal("20")
        )
        item["sum"] += normalized
        item["count"] += 1

    rows = []
    for item in buckets.values():
        average = (
            item["sum"] / item["count"]
            if item["count"]
            else Decimal("0")
        )
        rows.append({
            "id": item["id"],
            "name": item["name"],
            "average_on_20": round(float(average), 2),
            "scores_count": item["count"],
        })

    rows.sort(
        key=lambda item: (
            -item["average_on_20"],
            item["name"].lower(),
        )
    )
    return rows


def _classroom_academic_stats(
    *,
    school,
    classroom,
    active_period=None,
):
    assessments = Assessment.objects.filter(
        school=school,
        teaching_assignment__school=school,
        teaching_assignment__academic_year=classroom.academic_year,
        teaching_assignment__classroom=classroom,
    )
    if active_period:
        assessments_for_period = assessments.filter(
            academic_period_id=active_period["id"]
        )
    else:
        assessments_for_period = assessments

    status_counts = {
        row["status"]: row["count"]
        for row in assessments_for_period.values("status")
        .annotate(count=Count("id"))
        .order_by()
    }
    total = sum(status_counts.values())
    published = status_counts.get(
        Assessment.Status.PUBLISHED,
        0,
    )

    report_cards = ReportCardSnapshot.objects.filter(
        school=school,
        academic_year=classroom.academic_year,
        enrollment__classroom=classroom,
    )
    period_reports = (
        report_cards.filter(
            report_type=ReportCardSnapshot.ReportType.PERIOD
        )
        .values("enrollment_id", "academic_period_id")
        .distinct()
        .count()
    )
    annual_reports = (
        report_cards.filter(
            report_type=ReportCardSnapshot.ReportType.ANNUAL
        )
        .values("enrollment_id")
        .distinct()
        .count()
    )

    enrollments = Enrollment.objects.filter(
        school=school,
        academic_year=classroom.academic_year,
        classroom=classroom,
    )

    annual_average = (
        enrollments.filter(final_average__isnull=False)
        .aggregate(value=Avg("final_average"))
        .get("value")
    )

    decisions = {
        row["promotion_decision"]: row["count"]
        for row in enrollments.values("promotion_decision")
        .annotate(count=Count("id"))
        .order_by()
    }

    return {
        "assessments_total": total,
        "published_assessments": published,
        "publication_rate": _percent(published, total),
        "statuses": [
            {
                "key": status,
                "count": status_counts.get(status, 0),
                "percentage": _percent(
                    status_counts.get(status, 0),
                    total,
                ),
            }
            for status in [
                Assessment.Status.DRAFT,
                Assessment.Status.INPUT,
                Assessment.Status.SUBMITTED,
                Assessment.Status.VALIDATED,
                Assessment.Status.PUBLISHED,
            ]
        ],
        "published_report_cards": (
            period_reports + annual_reports
        ),
        "period_report_cards": period_reports,
        "annual_report_cards": annual_reports,
        "annual_average": (
            round(float(annual_average), 2)
            if annual_average is not None
            else None
        ),
        "promotion_decisions": [
            {
                "key": key,
                "count": decisions.get(key, 0),
            }
            for key in [
                Enrollment.PromotionDecision.PENDING,
                Enrollment.PromotionDecision.PROMOTED,
                Enrollment.PromotionDecision.REPEATED,
                Enrollment.PromotionDecision.GRADUATED,
                Enrollment.PromotionDecision.TRANSFERRED,
                Enrollment.PromotionDecision.WITHDRAWN,
            ]
            if decisions.get(key, 0)
        ],
        "subjects": _classroom_subject_performance(
            school=school,
            classroom=classroom,
            active_period=active_period,
        ),
    }


def _classroom_finance_stats(*, school, classroom):
    summary = finance_dashboard_summary(
        school=school,
        academic_year_id=classroom.academic_year_id,
        classroom_id=classroom.id,
    )

    currency = (
        StudentTuitionAccount.objects.filter(
            school=school,
            enrollment__academic_year=classroom.academic_year,
            enrollment__classroom=classroom,
        )
        .values_list("plan__currency", flat=True)
        .first()
        or "XAF"
    )

    return {
        "currency": currency,
        "expected_total": _money(summary["expected_total"]),
        "collected_total": _money(summary["collected_total"]),
        "outstanding_total": _money(
            summary["outstanding_total"]
        ),
        "collection_rate": float(summary["collection_rate"]),
        "accounts_count": summary["accounts_count"],
        "paid_count": summary["paid_count"],
        "partial_count": summary["partial_count"],
        "unpaid_count": summary["unpaid_count"],
        "payments_today": _money(summary["payments_today"]),
    }


def build_classroom_statistics(
    *,
    school,
    classroom,
    membership,
    user,
):
    if membership.role == SchoolMembership.Role.TEACHER:
        if not _classroom_teacher_scope_allowed(
            school=school,
            classroom=classroom,
            user=user,
        ):
            raise PermissionError(
                "Vous n'avez pas accès aux statistiques de cette classe."
            )

    active_period = _active_period(classroom.academic_year)

    students_count, gender = _classroom_gender_stats(
        school=school,
        classroom=classroom,
    )

    capacity = classroom.capacity
    occupancy_rate = (
        _percent(students_count, capacity)
        if capacity
        else None
    )

    teaching = _classroom_teaching_stats(
        school=school,
        classroom=classroom,
    )

    academics = None
    if membership.role in ACADEMIC_ROLES:
        academics = _classroom_academic_stats(
            school=school,
            classroom=classroom,
            active_period=active_period,
        )

    finance = None
    if membership.role in FINANCE_ROLES:
        finance = _classroom_finance_stats(
            school=school,
            classroom=classroom,
        )

    return {
        "classroom": {
            "id": classroom.id,
            "name": classroom.name,
            "code": classroom.code,
            "capacity": classroom.capacity,
            "is_active": classroom.is_active,
            "academic_year": {
                "id": classroom.academic_year_id,
                "name": classroom.academic_year.name,
            },
            "level": {
                "id": classroom.level_id,
                "name": classroom.level.name,
            },
            "cycle": {
                "id": classroom.level.cycle_id,
                "name": classroom.level.cycle.name,
                "kind": classroom.level.cycle.kind,
            },
            "section": {
                "id": classroom.level.cycle.section_id,
                "name": classroom.level.cycle.section.name,
                "language": (
                    classroom.level.cycle.section.language
                ),
            },
        },
        "active_period": active_period,
        "population": {
            "students": students_count,
            "capacity": capacity,
            "occupancy_rate": occupancy_rate,
            "gender": gender,
        },
        "teaching": teaching,
        "academics": academics,
        "finance": finance,
        "generated_at": timezone.now(),
    }

