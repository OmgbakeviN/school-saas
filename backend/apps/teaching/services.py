from django.db import transaction

from apps.accounts.models import SchoolMembership
from apps.academics.models import Classroom, LevelSubject
from apps.people.models import Teacher
from apps.tenants.models import School

from .models import ClassroomLeadership, TeachingAssignment


CLASS_TEACHER_MODELS = {
    School.TeachingModel.CLASS_TEACHER,
    School.TeachingModel.HYBRID,
}


def get_teacher_profile_for_user(*, user, school):
    if not user or not user.is_authenticated:
        return None

    return (
        Teacher.objects
        .filter(
            school=school,
            user=user,
            status=Teacher.Status.ACTIVE,
        )
        .first()
    )


def school_uses_class_teacher_access(school):
    """
    CLASS_TEACHER:
        le titulaire actif d'une classe peut enseigner toutes les matières
        actives du programme du niveau.

    HYBRID:
        la même règle s'applique au titulaire, tandis que des affectations
        manuelles peuvent coexister pour les spécialistes.

    SUBJECT_TEACHER:
        aucune autorisation implicite n'est accordée par le rôle de titulaire.
    """
    return school.teaching_model in CLASS_TEACHER_MODELS


def _context_auto_assignments(*, school, academic_year_id, classroom_id):
    return TeachingAssignment.objects.filter(
        school=school,
        academic_year_id=academic_year_id,
        classroom_id=classroom_id,
        source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
    )


@transaction.atomic
def sync_classroom_class_teacher_assignments(
    *,
    school,
    academic_year_id,
    classroom_id,
):
    """
    Synchronise les affectations dérivées d'un titulaire de classe.

    Les affectations automatiques sont matérialisées dans TeachingAssignment
    afin que les évaluations puissent continuer à référencer une affectation
    stable par clé étrangère.

    Elles ne sont jamais supprimées si elles ont servi dans l'historique :
    lorsqu'elles ne sont plus valides elles sont simplement désactivées.
    """
    classroom = (
        Classroom.objects
        .filter(
            school=school,
            id=classroom_id,
            academic_year_id=academic_year_id,
        )
        .select_related("level", "academic_year")
        .first()
    )

    auto_queryset = _context_auto_assignments(
        school=school,
        academic_year_id=academic_year_id,
        classroom_id=classroom_id,
    )

    if not classroom or not school_uses_class_teacher_access(school):
        disabled = auto_queryset.filter(is_active=True).update(is_active=False)
        return {
            "created": 0,
            "reactivated": 0,
            "disabled": disabled,
        }

    leadership = (
        ClassroomLeadership.objects
        .filter(
            school=school,
            academic_year_id=academic_year_id,
            classroom_id=classroom_id,
            role=ClassroomLeadership.Role.CLASS_TEACHER,
            is_active=True,
            teacher__status=Teacher.Status.ACTIVE,
        )
        .select_related("teacher")
        .first()
    )

    if not leadership:
        disabled = auto_queryset.filter(is_active=True).update(is_active=False)
        return {
            "created": 0,
            "reactivated": 0,
            "disabled": disabled,
        }

    subject_ids = list(
        LevelSubject.objects.filter(
            school=school,
            level_id=classroom.level_id,
            is_active=True,
            subject__is_active=True,
        ).values_list("subject_id", flat=True)
    )

    # Toute ancienne affectation automatique de cette classe qui ne
    # correspond plus au titulaire ou au programme est désactivée.
    disabled = auto_queryset.exclude(
        teacher_id=leadership.teacher_id,
        subject_id__in=subject_ids,
    ).filter(is_active=True).update(is_active=False)

    created = 0
    reactivated = 0

    for subject_id in subject_ids:
        existing = TeachingAssignment.objects.filter(
            school=school,
            academic_year_id=academic_year_id,
            teacher_id=leadership.teacher_id,
            subject_id=subject_id,
            classroom_id=classroom_id,
        ).first()

        # Une affectation MANUAL existante est un override explicite.
        # Elle reste sous le contrôle de l'administration.
        if existing and existing.source == TeachingAssignment.Source.MANUAL:
            continue

        if existing:
            changed_fields = []
            if not existing.is_active:
                existing.is_active = True
                changed_fields.append("is_active")
                reactivated += 1
            if not existing.can_enter_scores:
                existing.can_enter_scores = True
                changed_fields.append("can_enter_scores")
            if changed_fields:
                changed_fields.append("updated_at")
                existing.save(update_fields=changed_fields)
            continue

        TeachingAssignment.objects.create(
            school=school,
            academic_year_id=academic_year_id,
            teacher_id=leadership.teacher_id,
            subject_id=subject_id,
            classroom_id=classroom_id,
            source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
            can_enter_scores=True,
            is_active=True,
            notes="Accès généré automatiquement depuis le titulaire de classe.",
        )
        created += 1

    return {
        "created": created,
        "reactivated": reactivated,
        "disabled": disabled,
    }


@transaction.atomic
def sync_school_class_teacher_assignments(
    *,
    school,
    academic_year_id=None,
    classroom_id=None,
):
    """
    Synchronise les contextes qui ont un titulaire actif et les contextes
    qui possèdent déjà des affectations automatiques.

    Appelé à la lecture des affectations afin qu'une ancienne école primaire
    configurée avant STEP 05.1 soit mise à niveau sans commande manuelle.
    """
    leaderships = ClassroomLeadership.objects.filter(
        school=school,
        role=ClassroomLeadership.Role.CLASS_TEACHER,
    )
    auto = TeachingAssignment.objects.filter(
        school=school,
        source=TeachingAssignment.Source.CLASS_TEACHER_AUTO,
    )

    if academic_year_id:
        leaderships = leaderships.filter(academic_year_id=academic_year_id)
        auto = auto.filter(academic_year_id=academic_year_id)

    if classroom_id:
        leaderships = leaderships.filter(classroom_id=classroom_id)
        auto = auto.filter(classroom_id=classroom_id)

    contexts = set(
        leaderships.values_list("academic_year_id", "classroom_id")
    )
    contexts.update(
        auto.values_list("academic_year_id", "classroom_id")
    )

    total = {
        "created": 0,
        "reactivated": 0,
        "disabled": 0,
    }

    for year_id, class_id in contexts:
        result = sync_classroom_class_teacher_assignments(
            school=school,
            academic_year_id=year_id,
            classroom_id=class_id,
        )
        for key in total:
            total[key] += result[key]

    return total


def teacher_has_class_teacher_subject_access(
    *,
    teacher,
    school,
    academic_year_id,
    classroom_id,
    subject_id,
):
    if not school_uses_class_teacher_access(school):
        return False

    leadership_exists = ClassroomLeadership.objects.filter(
        school=school,
        academic_year_id=academic_year_id,
        classroom_id=classroom_id,
        teacher=teacher,
        role=ClassroomLeadership.Role.CLASS_TEACHER,
        is_active=True,
    ).exists()

    if not leadership_exists:
        return False

    classroom = Classroom.objects.filter(
        school=school,
        id=classroom_id,
        academic_year_id=academic_year_id,
    ).first()

    if not classroom:
        return False

    return LevelSubject.objects.filter(
        school=school,
        level_id=classroom.level_id,
        subject_id=subject_id,
        is_active=True,
        subject__is_active=True,
    ).exists()


def teacher_can_enter_scores(
    *,
    user,
    school,
    academic_year_id,
    classroom_id,
    subject_id,
):
    """
    Vérifie le droit effectif de saisie.

    Priorité :
      1. une affectation manuelle exacte est un override explicite ;
      2. une affectation automatique active du titulaire autorise ;
      3. fallback titulaire + matière du programme pour résilience.

    HOMEROOM_TEACHER / professeur principal n'accorde jamais, à lui seul,
    un droit de saisie des notes.
    """
    membership = SchoolMembership.objects.filter(
        school=school,
        user=user,
        is_active=True,
        role=SchoolMembership.Role.TEACHER,
    ).first()

    if not membership:
        return False

    teacher = get_teacher_profile_for_user(user=user, school=school)
    if not teacher:
        return False

    assignment = TeachingAssignment.objects.filter(
        school=school,
        teacher=teacher,
        academic_year_id=academic_year_id,
        classroom_id=classroom_id,
        subject_id=subject_id,
    ).first()

    if assignment:
        if assignment.source == TeachingAssignment.Source.MANUAL:
            return bool(
                assignment.is_active
                and assignment.can_enter_scores
            )

        if assignment.is_active and assignment.can_enter_scores:
            return True

    return teacher_has_class_teacher_subject_access(
        teacher=teacher,
        school=school,
        academic_year_id=academic_year_id,
        classroom_id=classroom_id,
        subject_id=subject_id,
    )
