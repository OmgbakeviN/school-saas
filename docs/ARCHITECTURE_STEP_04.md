# Architecture — STEP 04

## Découplage identité / compte / pédagogie

```text
accounts.User
    │
    ├── SchoolMembership(role=TEACHER)
    │
    └── people.Teacher.user
              │
              ├── TeachingAssignment
              │      ├── Subject
              │      ├── Classroom
              │      └── AcademicYear
              │
              └── ClassroomLeadership
                     ├── Classroom
                     ├── AcademicYear
                     └── role
```

`User` représente l'identité de connexion.

`SchoolMembership` représente l'autorisation d'entrer dans un tenant.

`Teacher` représente le profil métier permanent de l'enseignant dans un établissement.

`TeachingAssignment` représente le droit pédagogique précis pour une année.

## Principes retenus

1. Aucun accès aux notes ne dépend uniquement du rôle global `TEACHER`.
2. Une affectation matière/classe explicite est obligatoire.
3. Titulaire et professeur principal sont des responsabilités de classe, pas des permissions globales de notes.
4. Les enseignants ne peuvent lire que leurs propres affectations via `/api/teaching/me/`.
5. OWNER / DIRECTOR / MANAGER administrent les affectations.
6. Seuls OWNER / DIRECTOR gèrent les comptes de connexion enseignants.
7. Toutes les querysets sont filtrées par `request.school`.
8. Le compte enseignant peut être révoqué sans supprimer le profil ni l'historique.

## Préparation du module Assessments

Le futur module de notes devra utiliser :

```python
teacher_can_enter_scores(
    user=request.user,
    school=request.school,
    academic_year_id=...,
    classroom_id=...,
    subject_id=...,
)
```

Ce contrôle doit être exécuté côté backend même si le frontend masque déjà les écrans non autorisés.
