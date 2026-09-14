# STEP 07.4.1 — Statistiques détaillées par classe

## Objectif

Depuis le tableau de bord, chaque classe de l'année scolaire est maintenant
cliquable.

```text
Tableau de bord
→ Effectifs par classe
→ cliquer sur CM2 A
→ statistiques détaillées de CM2 A
```

La vue détaillée s'ouvre dans une modale responsive sans quitter le dashboard.

## Endpoint

```http
GET /api/tenant/dashboard/classrooms/{classroom_id}/statistics/
```

Le chemin est explicite afin de garder l'API lisible.

## Données affichées

### Population

- nombre d'élèves actifs ;
- capacité de la classe ;
- taux d'occupation ;
- répartition garçons / filles / autre / non renseigné.

### Équipe pédagogique

- nombre d'enseignants ;
- matières du programme ;
- enseignants affectés ;
- titulaire de classe / professeur principal ;
- matières de chaque enseignant.

Les matières du programme sont lues depuis `LevelSubject`, ce qui couvre aussi
le primaire lorsqu'un titulaire enseigne plusieurs matières sans nécessiter
une affectation explicite par matière.

### Statistiques pédagogiques

Pour les rôles autorisés :

- nombre d'évaluations ;
- workflow DRAFT / INPUT / SUBMITTED / VALIDATED / PUBLISHED ;
- taux de publication ;
- bulletins publiés ;
- moyenne annuelle de la classe si disponible ;
- décisions de promotion ;
- moyenne par matière.

La moyenne par matière est calculée uniquement à partir des évaluations
`PUBLISHED` de la période active. Chaque note est normalisée sur 20 afin de
pouvoir agréger des évaluations ayant des barèmes différents.

### Finance

Pour OWNER / DIRECTOR / MANAGER / ACCOUNTANT :

- pension attendue pour la classe ;
- montant encaissé ;
- reste à encaisser ;
- taux de recouvrement ;
- comptes soldés / partiels / impayés.

## Permissions

### Direction / gestion

Accès aux statistiques des classes de l'établissement.

### Enseignant

Un enseignant peut ouvrir uniquement les classes pour lesquelles il possède :

```text
TeachingAssignment
ou
ClassroomLeadership
```

Une tentative d'accès à une autre classe retourne :

```http
403 Forbidden
```

### Comptable

Accès à la population et aux statistiques financières. Les statistiques
académiques détaillées restent masquées.

## Multi-tenant

Le backend recherche toujours la classe avec :

```text
school=request.school
```

Une classe d'un autre établissement ne peut donc pas être ouverte via son ID.

## Interface

La liste « Effectifs par classe » contient maintenant toutes les classes
actives de l'année et devient scrollable lorsqu'elle est longue.

Le clic ouvre une modale plein écran sur mobile et large sur desktop.
La couleur et les accents reprennent toujours le thème de l'établissement.

## Migration

Aucune migration.
