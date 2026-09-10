# STEP 05 — Évaluations & notes

## Objectif

STEP 05 transforme les affectations pédagogiques de STEP 04 en un système sécurisé de saisie et de validation des résultats.

## Modèles

### AssessmentPeriodControl

Contrôle administratif de la période de saisie :

```text
School
  └── AcademicPeriod
        └── score_entry_open
```

L'ouverture d'un trimestre/semestre ne dépend donc pas du professeur.

### Assessment

```text
TeachingAssignment
  = Teacher + Subject + Classroom + AcademicYear
          +
AcademicPeriod
          ↓
Assessment
```

Une évaluation possède : titre, type, date, barème, poids et statut.

### Grade

Une note est liée à `Enrollment`, et non directement à `Student` :

```text
Assessment + Enrollment → Grade
```

Cela garantit que la note reste attachée à la bonne année scolaire et à la bonne classe.

## Workflow

```text
DRAFT
  ↓ ouverture
INPUT
  ↓ enseignant soumet
SUBMITTED
  ↓ direction valide
VALIDATED
  ↓ direction publie
PUBLISHED
```

Une évaluation `PUBLISHED` est verrouillée.

La direction peut exécuter :

```text
PUBLISHED → INPUT
```

avec l'action de réouverture. Cette action est journalisée via `reopened_by` et `reopened_at`.

## Saisie enseignant

La saisie ne repose jamais uniquement sur le rôle `TEACHER`.

Le backend appelle la logique de STEP 04 et exige l'affectation exacte :

```text
enseignant + matière + classe + année
```

avec :

```text
can_enter_scores = True
```

Un professeur principal ou titulaire ne reçoit aucun accès implicite aux autres matières.

## Carnet de notes

Le carnet charge les `Enrollment` de la classe et permet :

```text
note numérique
ABS
DISPENSÉ
commentaire
```

La soumission est refusée si un élève n'a ni note, ni absence, ni dispense.

## Calcul des moyennes

Seules les évaluations `PUBLISHED` sont comptées.

Une évaluation peut avoir son propre barème, par exemple :

```text
Interrogation /10
Devoir /20
Examen /40
```

Avant agrégation, chaque note est normalisée vers le barème effectif de la matière (`LevelSubject.max_score_override`, puis Level, Cycle, School policy).

Ensuite :

```text
moyenne matière = moyenne pondérée par Assessment.weight
moyenne période = moyenne pondérée par LevelSubject.coefficient
moyenne annuelle = moyenne pondérée par AcademicPeriod.weight
```

Le recalcul annuel peut alimenter :

```text
Enrollment.final_average
```

qui est déjà utilisé par l'assistant de promotion de STEP 03.2.

## Permissions

### TEACHER

- voit uniquement ses évaluations ;
- crée des évaluations uniquement sur ses affectations autorisées ;
- saisit uniquement lorsque le statut est `INPUT` ;
- soumet à la direction ;
- ne valide pas ;
- ne publie pas ;
- ne rouvre pas.

### MANAGER

- voit et administre les évaluations ;
- contrôle les périodes de saisie ;
- peut aider à la saisie ;
- ne réalise pas la validation finale / publication.

### OWNER / DIRECTOR

- contrôle les périodes ;
- valide ;
- publie ;
- rouvre une évaluation verrouillée.

## API

Préfixe :

```text
/api/assessments/
```

Voir `docs/SWAGGER_STEP_05.md`.

## Adaptation STEP 05.1 — primaire / titulaire

En mode `CLASS_TEACHER` ou `HYBRID`, le titulaire actif d'une classe
reçoit automatiquement les matières actives du `LevelSubject` de son niveau.

Il peut donc créer une évaluation pour chacune de ces matières sans que la
direction crée manuellement une affectation par matière.

Voir `docs/STEP_05_1_TITULAIRE_PRIMAIRE.md`.

