from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership
from apps.academics.models import AcademicPolicy, LevelSubject
from apps.people.models import Enrollment
from apps.teaching.services import (
    get_teacher_profile_for_user,
    teacher_can_enter_scores,
)

from .models import Assessment, AssessmentPeriodControl, Grade


THREE_PLACES = Decimal("0.001")
TWO_PLACES = Decimal("0.01")


def quantize(value, places=THREE_PLACES):
    if value is None:
        return None
    return Decimal(value).quantize(places, rounding=ROUND_HALF_UP)


def get_period_control(*, school, academic_period):
    control, _ = AssessmentPeriodControl.objects.get_or_create(
        school=school,
        academic_period=academic_period,
    )
    return control


def user_is_assessment_manager(request):
    membership = get_school_membership(request)
    return bool(
        membership
        and membership.role
        in {
            SchoolMembership.Role.OWNER,
            SchoolMembership.Role.DIRECTOR,
            SchoolMembership.Role.MANAGER,
        }
    )


def user_is_direction(request):
    membership = get_school_membership(request)
    return bool(
        membership
        and membership.role
        in {
            SchoolMembership.Role.OWNER,
            SchoolMembership.Role.DIRECTOR,
        }
    )


def teacher_owns_assessment(*, user, school, assessment):
    """
    Ownership is historical: a teacher keeps read access to assessments they
    created/worked on even if a derived assignment is later deactivated.

    Editing remains protected separately by teacher_can_work_on_assessment().
    """
    teacher = get_teacher_profile_for_user(user=user, school=school)
    return bool(
        teacher
        and assessment.teaching_assignment.teacher_id == teacher.id
    )


def teacher_can_work_on_assessment(*, user, school, assessment):
    return teacher_can_enter_scores(
        user=user,
        school=school,
        academic_year_id=assessment.teaching_assignment.academic_year_id,
        classroom_id=assessment.teaching_assignment.classroom_id,
        subject_id=assessment.teaching_assignment.subject_id,
    )


def can_view_assessment(*, request, assessment):
    if user_is_assessment_manager(request):
        return True
    return teacher_owns_assessment(
        user=request.user,
        school=request.school,
        assessment=assessment,
    )


def can_edit_assessment_metadata(*, request, assessment):
    if assessment.status not in {
        Assessment.Status.DRAFT,
        Assessment.Status.INPUT,
    }:
        return False
    if user_is_assessment_manager(request):
        return True
    return teacher_can_work_on_assessment(
        user=request.user,
        school=request.school,
        assessment=assessment,
    )


def can_edit_gradebook(*, request, assessment):
    if assessment.status != Assessment.Status.INPUT:
        return False

    if user_is_assessment_manager(request):
        return True

    if not teacher_can_work_on_assessment(
        user=request.user,
        school=request.school,
        assessment=assessment,
    ):
        return False

    control = get_period_control(
        school=request.school,
        academic_period=assessment.academic_period,
    )
    return bool(control.score_entry_open or assessment.reopened_at)


def effective_subject_scale(*, school, level, subject):
    config = LevelSubject.objects.filter(
        school=school,
        level=level,
        subject=subject,
        is_active=True,
    ).select_related("level__cycle").first()

    policy, _ = AcademicPolicy.objects.get_or_create(school=school)

    if config and config.max_score_override is not None:
        max_score = config.max_score_override
    elif level.max_score_override is not None:
        max_score = level.max_score_override
    elif level.cycle.max_score_override is not None:
        max_score = level.cycle.max_score_override
    else:
        max_score = policy.default_max_score

    coefficient = config.coefficient if config else Decimal("1")
    return Decimal(max_score), Decimal(coefficient)


def calculate_subject_average(*, enrollment, academic_period, subject):
    assessments = list(
        Assessment.objects.filter(
            school=enrollment.school,
            teaching_assignment__academic_year=enrollment.academic_year,
            teaching_assignment__classroom=enrollment.classroom,
            teaching_assignment__subject=subject,
            academic_period=academic_period,
            status=Assessment.Status.PUBLISHED,
        ).select_related("teaching_assignment")
    )

    if not assessments:
        return None

    subject_max, coefficient = effective_subject_scale(
        school=enrollment.school,
        level=enrollment.classroom.level,
        subject=subject,
    )

    grades = {
        grade.assessment_id: grade
        for grade in Grade.objects.filter(
            school=enrollment.school,
            assessment__in=assessments,
            enrollment=enrollment,
        )
    }

    weighted_sum = Decimal("0")
    total_weight = Decimal("0")
    counted_assessments = 0

    for assessment in assessments:
        grade = grades.get(assessment.id)
        if (
            not grade
            or grade.score is None
            or grade.is_absent
            or grade.is_exempt
        ):
            continue

        normalized = (
            Decimal(grade.score)
            / Decimal(assessment.max_score)
            * subject_max
        )
        weighted_sum += normalized * Decimal(assessment.weight)
        total_weight += Decimal(assessment.weight)
        counted_assessments += 1

    if total_weight == 0:
        return None

    return {
        "average": quantize(weighted_sum / total_weight),
        "max_score": quantize(subject_max, TWO_PLACES),
        "coefficient": quantize(coefficient),
        "assessment_count": counted_assessments,
    }


def calculate_period_result(*, enrollment, academic_period, allowed_subject_ids=None):
    published_subject_ids = set(
        Assessment.objects.filter(
            school=enrollment.school,
            teaching_assignment__academic_year=enrollment.academic_year,
            teaching_assignment__classroom=enrollment.classroom,
            academic_period=academic_period,
            status=Assessment.Status.PUBLISHED,
        ).values_list("teaching_assignment__subject_id", flat=True)
    )

    if allowed_subject_ids is not None:
        published_subject_ids &= set(allowed_subject_ids)

    configs = {
        config.subject_id: config
        for config in LevelSubject.objects.filter(
            school=enrollment.school,
            level=enrollment.classroom.level,
            subject_id__in=published_subject_ids,
            is_active=True,
        ).select_related("subject", "level__cycle")
    }

    subject_rows = []
    overall_sum = Decimal("0")
    coefficient_sum = Decimal("0")

    # Include configured subjects first; fall back to subject ids if an old
    # assignment exists without a LevelSubject row.
    subject_ids = list(configs.keys())
    for subject_id in sorted(published_subject_ids - set(subject_ids)):
        subject_ids.append(subject_id)

    from apps.academics.models import Subject

    subject_map = {
        item.id: item
        for item in Subject.objects.filter(
            school=enrollment.school,
            id__in=subject_ids,
        )
    }

    for subject_id in subject_ids:
        subject = subject_map.get(subject_id)
        if not subject:
            continue

        result = calculate_subject_average(
            enrollment=enrollment,
            academic_period=academic_period,
            subject=subject,
        )
        if not result:
            continue

        subject_rows.append({
            "subject_id": subject.id,
            "subject_name": subject.name,
            **result,
        })

        overall_sum += Decimal(result["average"]) * Decimal(result["coefficient"])
        coefficient_sum += Decimal(result["coefficient"])

    overall_average = None
    if coefficient_sum > 0:
        overall_average = quantize(overall_sum / coefficient_sum)

    return {
        "period_id": academic_period.id,
        "period_name": academic_period.name,
        "period_weight": quantize(academic_period.weight),
        "subjects": subject_rows,
        "overall_average": overall_average,
    }


def calculate_year_average(*, enrollment):
    period_rows = []
    weighted_sum = Decimal("0")
    total_weight = Decimal("0")

    for period in enrollment.academic_year.periods.filter(is_active=True).order_by("order"):
        result = calculate_period_result(
            enrollment=enrollment,
            academic_period=period,
        )
        if result["overall_average"] is None:
            continue

        weight = Decimal(period.weight)
        weighted_sum += Decimal(result["overall_average"]) * weight
        total_weight += weight
        period_rows.append(result)

    annual_average = None
    if total_weight > 0:
        annual_average = quantize(weighted_sum / total_weight)

    return annual_average, period_rows


@transaction.atomic
def recalculate_enrollment_year_average(enrollment):
    annual_average, period_rows = calculate_year_average(enrollment=enrollment)
    enrollment.final_average = annual_average
    enrollment.save(update_fields=["final_average", "updated_at"])
    return annual_average, period_rows


@transaction.atomic
def recalculate_year_averages(*, school, academic_year, classroom=None):
    queryset = Enrollment.objects.filter(
        school=school,
        academic_year=academic_year,
    ).select_related(
        "student",
        "classroom",
        "classroom__level",
        "classroom__level__cycle",
        "academic_year",
    )

    if classroom is not None:
        queryset = queryset.filter(classroom=classroom)

    updated = 0
    with_average = 0

    for enrollment in queryset:
        average, _ = recalculate_enrollment_year_average(enrollment)
        updated += 1
        if average is not None:
            with_average += 1

    return {
        "updated": updated,
        "with_average": with_average,
    }


def incomplete_grade_count(assessment):
    enrollment_ids = set(
        Enrollment.objects.filter(
            school=assessment.school,
            academic_year=assessment.teaching_assignment.academic_year,
            classroom=assessment.teaching_assignment.classroom,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).values_list("id", flat=True)
    )

    completed_ids = set(
        Grade.objects.filter(
            school=assessment.school,
            assessment=assessment,
        ).filter(
            models_complete_grade_filter()
        ).values_list("enrollment_id", flat=True)
    )

    return len(enrollment_ids - completed_ids)


def models_complete_grade_filter():
    from django.db.models import Q

    return (
        Q(score__isnull=False)
        | Q(is_absent=True)
        | Q(is_exempt=True)
    )
