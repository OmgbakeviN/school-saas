# STEP 04 — Affectations pédagogiques

## Objectif

Cette étape relie les profils enseignants aux matières, classes et années scolaires réellement enseignées.

Le modèle pédagogique est volontairement séparé en deux concepts :

```text
TeachingAssignment
Teacher + Subject + Classroom + AcademicYear
```

et :

```text
ClassroomLeadership
Teacher + Classroom + AcademicYear + Role
```

Cette séparation évite de donner automatiquement des droits sur toutes les matières à un titulaire de classe ou à un professeur principal.

## TeachingAssignment

Champs principaux :

```text
school
academic_year
teacher
subject
classroom
can_enter_scores
is_active
notes
```

Une matière ne peut être affectée à un enseignant que si cette matière est déjà configurée dans `LevelSubject` pour le niveau de la classe.

La classe doit obligatoirement appartenir à la même année scolaire que l'affectation.

## Titulaire de classe / professeur principal

`ClassroomLeadership` contient deux rôles :

```text
CLASS_TEACHER      -> Titulaire de classe
HOMEROOM_TEACHER   -> Professeur principal
```

Une classe ne peut avoir qu'un responsable actif de chaque type pour une année scolaire donnée.

Le responsable de classe n'obtient pas automatiquement les droits de saisie des notes de toutes les matières.

## Permissions de saisie

La permission est portée par `TeachingAssignment.can_enter_scores`.

Le helper réutilisable :

```python
from apps.teaching.services import teacher_can_enter_scores
```

vérifie strictement :

```text
compte utilisateur
+ membership TEACHER actif
+ profil Teacher lié
+ année scolaire
+ classe
+ matière
+ affectation active
+ can_enter_scores = True
```

Le futur module `assessments` devra appeler ce helper avant toute création ou modification de note.

## Login des enseignants

Il n'existe pas un second système d'authentification pour les enseignants.

Tous les utilisateurs passent par le même modèle :

```text
User
  ↓
SchoolMembership
  ↓ role = TEACHER
Teacher.user
```

Le profil pédagogique `Teacher` reste séparé du compte de connexion `User`.

### Création du compte

La direction ouvre :

```text
Affectations pédagogiques
→ Comptes enseignants
```

Puis sélectionne un enseignant et choisit **Créer / lier le compte**.

Si l'e-mail n'existe pas encore :

```text
User créé
+ SchoolMembership(role=TEACHER)
+ Teacher.user lié
```

Si l'e-mail correspond déjà à un utilisateur BE WISE :

```text
User existant conservé
+ membership TEACHER créé/réactivé si nécessaire
+ Teacher.user lié
```

Le mot de passe d'un utilisateur existant n'est jamais modifié automatiquement.

### Connexion du professeur

Le professeur ouvre exactement le même portail que l'établissement :

```text
bws.localhost:5173
```

ou en production :

```text
bws.domaine-de-la-plateforme.com
```

Il se connecte avec son e-mail et son mot de passe habituel.

L'endpoint reste :

```text
POST /api/auth/login/
```

Le JWT contient le même utilisateur, mais le backend retrouve son `SchoolMembership` avec le rôle `TEACHER`.

### Ce que voit un professeur

Le menu professeur contient notamment :

```text
Tableau de bord
Structure académique (lecture)
Mes enseignements
Établissement (lecture)
Mon compte
```

Il ne voit pas :

```text
Personnes & inscriptions
Équipe & accès
gestion globale des affectations
```

`GET /api/teaching/me/` ne renvoie que ses propres affectations et responsabilités.

## Mot de passe

Tous les utilisateurs authentifiés peuvent changer leur propre mot de passe :

```text
POST /api/auth/change-password/
```

Interface :

```text
Mon compte
→ Mot de passe
```

Pour un nouveau professeur, la direction peut définir un mot de passe initial lors de la création du compte. Il est recommandé que l'enseignant le change à sa première connexion.

## Révocation d'accès

La direction peut révoquer le compte depuis l'écran des comptes enseignants.

La révocation :

```text
conserve Teacher
conserve User
retire Teacher.user
met SchoolMembership TEACHER en inactif
```

Les données pédagogiques et historiques ne sont donc jamais supprimées.

## Endpoints

```text
GET/POST   /api/teaching/assignments/
GET/PATCH/DELETE /api/teaching/assignments/<id>/

GET/POST   /api/teaching/leaderships/
GET/PATCH/DELETE /api/teaching/leaderships/<id>/

GET        /api/teaching/me/

POST       /api/teaching/teachers/<teacher_id>/account/
DELETE     /api/teaching/teachers/<teacher_id>/account/

POST       /api/auth/change-password/
```

Tous ces endpoints apparaissent dans Swagger sous le groupe `Teaching` ou `Authentication`.
