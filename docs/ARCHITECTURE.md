# Architecture — BE WISE School SaaS

## Architecture actuelle

```text
Browser
   |
   | slug.localhost:5173
   | ou slug.<domaine-courant>
   v
React / Vite
   |
   | X-Tenant-Slug uniquement en DEBUG
   v
Django REST Framework
   |
   | TenantResolutionMiddleware
   v
request.school
   |
   +--> tenants
   +--> accounts
   +--> futurs modules
   v
SQLite local / PostgreSQL production
```

## Adresse des établissements

Le frontend n'affiche plus deux adresses.

Il calcule une seule URL depuis l'environnement actuel :

```text
localhost:5173
  -> saint-joseph.localhost:5173
```

Si le SaaS est ensuite installé sur :

```text
prototype.bewiseinnovation.com
```

le portail généré devient :

```text
saint-joseph.prototype.bewiseinnovation.com
```

Django utilise `BASE_DOMAIN` pour résoudre ces sous-domaines en production.

## Multi-tenant

La règle reste :

```python
Model.objects.filter(school=request.school)
```

Les permissions contrôlent aussi l'appartenance active du compte au tenant.

Le header `X-Tenant-Slug` n'est accepté qu'en `DEBUG=True`.

## Applications backend

```text
core/
tenants/
accounts/

academics/       # étape 2
people/          # étape 3
teaching/        # étape 4
assessments/     # étape 5
report_cards/    # étape 5
finance/         # étape 6
analytics/       # étape 6
communications/  # étape 7
```

## Branding

`School` possède désormais :

```text
logo
motto
primary_color
secondary_color
```

Ces champs deviendront la source de branding pour :

- portail ;
- bulletins ;
- reçus ;
- pages publiques de vérification.

## Équipe et autorisations

`SchoolMembership` reste distinct de `User`.

Rôles actuels :

```text
OWNER
DIRECTOR
MANAGER
TEACHER
ACCOUNTANT
```

Administration de l'établissement :

```text
OWNER
DIRECTOR
```

Les profils métier détaillés `Teacher`, `Parent`, etc. seront créés à l'étape 3. Un compte utilisateur et un profil métier ne sont pas la même chose.


---

# Étape 2 — Architecture académique

## Hiérarchie

```text
School
  |
  +-- AcademicYear
  |
  +-- Section
       |
       +-- Cycle
            |
            +-- Level
                 |
                 +-- Classroom (pour une AcademicYear)
```

### Pourquoi `Classroom` dépend de l'année

`3e A` en 2026/2027 et `3e A` en 2027/2028 ne sont pas le même groupe d'élèves.

Le niveau `3e` reste une configuration permanente, tandis que la classe annuelle est recréée pour chaque année scolaire.

Cela permettra ensuite de rattacher proprement :

- inscriptions ;
- affectations pédagogiques ;
- notes ;
- statistiques annuelles.

## École bilingue

Une école bilingue peut posséder plusieurs sections :

```text
Section francophone
  → Primaire
  → Secondaire

English section
  → Primary
  → Secondary
```

Le système n'impose pas cette structure : le générateur crée une suggestion modifiable.

Une section `BILINGUAL` peut également être créée manuellement pour les établissements dont une même filière utilise les deux langues.

## Isolation

Toutes les entités académiques possèdent explicitement un `school_id`.

Les serializers refusent d'associer :

- un cycle à une section d'une autre école ;
- un niveau à un cycle d'une autre école ;
- une classe à une année ou un niveau d'une autre école.


---

# Étape 2.2 — Programme académique

## Périodes

```text
AcademicYear
  ↓
AcademicPeriod
    - Trimestre
    - Semestre
    - Custom
```

Une `AcademicPeriod` n'est PAS une séquence ou un examen.

Plus tard :

```text
AcademicPeriod
  ↓
AssessmentWindow / Evaluation
    - Séquence
    - Examen
    - Composition
```

La direction créera ces évaluations à l'Étape 5.

## Matières

```text
Subject
```

est le catalogue de l'établissement.

```text
LevelSubject
```

est la configuration pédagogique :

```text
Level + Subject + coefficient + langue + note max éventuelle
```

Exemple :

```text
3e
  + Mathématiques
  + coefficient 4
  + /20
```

La classe annuelle ne porte pas le coefficient. Cela évite de recopier le programme dans 3e A, 3e B, 3e C.

## Notation

```text
AcademicPolicy
```

contient la règle de l'établissement :

```text
default_max_score
default_promotion_threshold
```

Les cycles et niveaux peuvent la remplacer.

Ordre de résolution :

```text
niveau
  ↓ si absent
cycle
  ↓ si absent
établissement
```

Une matière/niveau peut aussi remplacer la note maximale pour des cas spécifiques.

## Refresh UI

Les composants académiques ne remplacent plus toute leur interface par un loader après une mutation.

Après création/suppression :

```text
POST/DELETE
  ↓
refresh API silencieux
  ↓
state React mis à jour
```

Le loader plein écran est uniquement utilisé au premier chargement.


---

# Affectations multiples de matières

Le client n'envoie pas une requête par niveau.

Il utilise :

```text
POST /api/academics/level-subjects/bulk/
```

avec :

```text
Subject
+ N Level IDs
+ coefficient commun
+ note max éventuelle
+ langue
```

Le backend traite l'ensemble dans une transaction.

Cela évite :

```text
20 niveaux = 20 requêtes HTTP
```

et conserve une API adaptée aux imports et futures opérations de masse.

Les dialogues de modification utilisent les endpoints REST existants :

```text
PATCH /api/academics/subjects/{id}/
PATCH /api/academics/level-subjects/{id}/
```


---

# Étape 3.1 — Personnes & inscriptions

## Séparation identité / historique scolaire

```text
Student
   |
   +-- Enrollment 2026/2027
   |      └-- Classroom: 3e A
   |
   +-- Enrollment 2027/2028
          └-- Classroom: 2nde B
```

`Student` représente la personne.

`Enrollment` représente sa situation scolaire pour une année précise.

Cette séparation rend possible :

- promotion ;
- redoublement ;
- transfert ;
- changement de classe ;
- historique pluriannuel ;
- statistiques longitudinales.

## Enseignants

```text
Teacher
```

est un profil métier distinct de :

```text
accounts.User
```

Un enseignant peut donc être enregistré sans compte de connexion.

Plus tard, un compte `User` pourra être lié au profil pour permettre l'accès à la saisie des notes.

## Parents / tuteurs

```text
Guardian
   ↓
StudentGuardian
   ↓
Student
```

Le lien porte les autorisations :

```text
relationship
is_primary
receives_notifications
can_receive_results
```

Le téléphone est stocké sur `Guardian`, ce qui préparera l'identification WhatsApp.

## Enrollment

Une inscription contient :

```text
school
student
academic_year
classroom
status
final_average
promotion_decision
decision_reason
next_enrollment
```

La contrainte principale est :

```text
1 student + 1 academic year = 1 enrollment maximum
```

La classe doit appartenir à la même année scolaire que l'inscription.

## Permissions

La gestion des personnes est actuellement ouverte à :

```text
OWNER
DIRECTOR
MANAGER
```

Les enseignants n'accèdent pas encore globalement aux données personnelles.

À l'étape 4, ils auront uniquement un accès pédagogique aux élèves de leurs propres classes.
