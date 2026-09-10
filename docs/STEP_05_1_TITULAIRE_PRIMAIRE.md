# STEP 05.1 — Adaptation Titulaire de classe / Primaire

## Objectif

Une école configurée avec :

```text
teaching_model = CLASS_TEACHER
```

ne doit pas créer manuellement une affectation par matière pour le
titulaire d'une classe.

Exemple :

```text
Mme NGONO
  ↓ titulaire
CM2 A
  ↓
Mathématiques
Français
Sciences
Histoire
Géographie
Anglais
...
```

Toutes les matières actives de `LevelSubject` du niveau sont disponibles
pour les évaluations.

## Modèles concernés

Le rôle titulaire reste stocké dans :

```text
ClassroomLeadership
role = CLASS_TEACHER
```

Les droits matière sont matérialisés dans `TeachingAssignment` avec :

```text
source = CLASS_TEACHER_AUTO
```

Cela permet à `Assessment.teaching_assignment` de conserver sa clé
étrangère existante sans modifier tout le moteur d'évaluation.

## Pourquoi matérialiser les droits ?

L'affectation automatique reste une vraie ligne de base de données afin que :

- les évaluations historiques gardent une référence stable ;
- Swagger et le frontend utilisent le même modèle que les affectations manuelles ;
- le carnet de notes ne nécessite aucun cas spécial ;
- les moyennes existantes restent inchangées.

Lorsqu'un titulaire change, les anciennes affectations automatiques ne sont
pas supprimées : elles sont désactivées afin de préserver l'historique.

## Synchronisation

La synchronisation se déclenche notamment :

- à la création d'un titulaire ;
- à la modification d'un titulaire ;
- à la suppression d'un titulaire ;
- à l'ouverture de `/api/teaching/me/` ;
- à la lecture des affectations par l'administration.

Cela permet aussi de mettre à niveau les titulaires créés avant STEP 05.1.

## Modèles pédagogiques

### CLASS_TEACHER

Un `CLASS_TEACHER` actif reçoit automatiquement toutes les matières actives
du programme du niveau de sa classe.

### SUBJECT_TEACHER

Aucun droit implicite. Une `TeachingAssignment` manuelle est obligatoire.

### HYBRID

Les deux mécanismes coexistent :

```text
Titulaire
  → matières du programme automatiquement

Spécialiste
  → affectation manuelle ciblée
```

## Professeur principal

`HOMEROOM_TEACHER` reste une responsabilité de classe.

Il ne donne jamais automatiquement accès aux notes d'une matière.

## Évaluations

Dans le formulaire de création d'une évaluation, le titulaire voit maintenant
toutes les matières générées automatiquement pour sa classe.

L'option ressemble à :

```text
Mathématiques • CM2 A • Mme NGONO • accès titulaire
Français • CM2 A • Mme NGONO • accès titulaire
Sciences • CM2 A • Mme NGONO • accès titulaire
```

Le reste du workflow ne change pas :

```text
DRAFT
  ↓
INPUT
  ↓
SUBMITTED
  ↓
VALIDATED
  ↓
PUBLISHED
```

## Sécurité

Le backend vérifie toujours le droit effectif de saisie.

Pour un titulaire :

```text
TEACHER actif
  +
Teacher.user
  +
CLASS_TEACHER actif
  +
classe / année exactes
  +
matière active dans LevelSubject
```

Pour un enseignant par matière :

```text
TeachingAssignment MANUAL active
  +
can_enter_scores = True
```

Aucune autorisation n'est décidée uniquement par le frontend.


## Synchroniser immédiatement les titulaires existants

Après migration :

```powershell
python manage.py sync_class_teacher_assignments
```

Pour une école précise :

```powershell
python manage.py sync_class_teacher_assignments --school bws
```

Ce n'est pas obligatoire pour le fonctionnement : `/api/teaching/me/` et
`/api/teaching/assignments/` effectuent aussi la synchronisation. La commande
permet simplement de matérialiser les accès immédiatement.
