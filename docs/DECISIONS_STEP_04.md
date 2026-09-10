# Décisions d'architecture — STEP 04

## ADR-031 — TeachingAssignment est annuel

Une affectation pédagogique contient explicitement `AcademicYear` même si `Classroom` possède déjà son année.

Cette redondance contrôlée facilite les filtres, permissions et futures requêtes de notes. Le serializer vérifie que les deux années correspondent.

## ADR-032 — Responsabilité de classe séparée des matières

`ClassroomLeadership` est séparé de `TeachingAssignment`.

Un titulaire ou professeur principal n'obtient donc pas implicitement le droit de modifier toutes les matières de la classe.

## ADR-033 — Un seul système de login

Les enseignants utilisent `accounts.User`, JWT et le portail tenant existant.

Aucune table d'authentification spécifique aux professeurs n'est introduite.

## ADR-034 — Teacher reste distinct de User

Le profil `people.Teacher` peut exister sans compte utilisateur.

Cela permet d'enregistrer un enseignant avant de lui ouvrir l'accès à la plateforme et de conserver son historique après révocation du compte.

## ADR-035 — Affectation explicite pour la saisie des notes

Un rôle `TEACHER` ne suffit jamais à autoriser la saisie.

Le backend doit trouver une `TeachingAssignment` active avec `can_enter_scores=True` pour le triplet classe + matière + année.

## ADR-036 — Les comptes enseignants sont administrés depuis Teaching

L'interface générique `Équipe & accès` n'est plus l'endroit recommandé pour créer un enseignant.

La création/liaison se fait depuis le profil métier afin d'éviter les comptes TEACHER sans `Teacher.user` associé.
