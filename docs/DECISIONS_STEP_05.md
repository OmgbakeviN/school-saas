# Décisions — STEP 05

## ADR-031 — Grade lié à Enrollment

Une note appartient à une inscription annuelle et non au Student permanent. Cela évite toute ambiguïté entre deux années scolaires.

## ADR-032 — Période de saisie contrôlée par l'administration

`AssessmentPeriodControl` sépare le calendrier académique (`AcademicPeriod`) du droit opérationnel de saisir des notes.

## ADR-033 — Le professeur principal n'obtient pas les notes des autres matières

Les permissions de saisie passent exclusivement par `TeachingAssignment.can_enter_scores`.

## ADR-034 — Publication = verrouillage

Une évaluation publiée n'est plus éditable. La correction exige une action de réouverture OWNER / DIRECTOR.

## ADR-035 — Seules les évaluations publiées entrent dans les moyennes

Un brouillon, une saisie en cours, une soumission ou une validation non publiée ne doit jamais modifier un bulletin ou une moyenne officielle.

## ADR-036 — Barèmes d'évaluation normalisés avant agrégation

Une note /10 et une note /40 peuvent coexister. Elles sont d'abord normalisées vers le barème effectif de la matière, puis pondérées.

## ADR-037 — Enrollment.final_average reste un cache administratif

La source de vérité reste le moteur `assessments`. `Enrollment.final_average` est recalculable et sert notamment au workflow de promotion.

## ADR — STEP 05.1 — matérialiser les droits du titulaire

**Décision :** conserver `Assessment.teaching_assignment` comme référence
unique et générer des `TeachingAssignment` de source
`CLASS_TEACHER_AUTO`.

**Raisons :**
- ne pas dupliquer le moteur de notes entre primaire et secondaire ;
- conserver une FK stable pour l'historique ;
- garder le même workflow de sécurité ;
- permettre au mode HYBRID de combiner titulaire et spécialistes.

`HOMEROOM_TEACHER` n'est pas une source d'autorisation de notes.

