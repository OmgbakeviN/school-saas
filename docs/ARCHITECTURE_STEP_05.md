# Architecture — STEP 05

## Chaîne métier

```text
School
 ├── AcademicYear
 │    ├── AcademicPeriod
 │    └── Classroom
 │          └── Enrollment
 └── TeachingAssignment
        ├── Teacher
        ├── Subject
        ├── Classroom
        └── AcademicYear
             ↓
         Assessment
             ↓
           Grade
```

## Invariants importants

1. `Assessment.school == TeachingAssignment.school == AcademicPeriod.school`.
2. La période de l'évaluation appartient à la même année que l'affectation.
3. `Grade.enrollment.classroom` correspond à la classe de l'affectation.
4. `Grade.enrollment.academic_year` correspond à l'année de l'affectation.
5. Une seule note existe par `Assessment + Enrollment`.
6. Les calculs académiques consomment uniquement les évaluations `PUBLISHED`.
7. Une réouverture ne modifie pas l'historique Student / Enrollment.

## Préparation STEP 06

Le module bulletin ne devra pas recalculer les notes lui-même. Il appellera les services de `apps.assessments` puis matérialisera les résultats dans un snapshot de bulletin.

## Extension STEP 05.1 — droits dérivés du titulaire

`TeachingAssignment` possède maintenant une provenance :

```text
MANUAL
CLASS_TEACHER_AUTO
```

Les affectations `CLASS_TEACHER_AUTO` sont dérivées de :

```text
School.teaching_model
  +
ClassroomLeadership(CLASS_TEACHER)
  +
Classroom.level
  +
LevelSubject actifs
```

Elles sont matérialisées mais gérées automatiquement.

Une suppression ou modification du titulaire désactive les anciennes
affectations dérivées au lieu de supprimer l'historique.

