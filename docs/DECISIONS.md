# Décisions d'architecture

## ADR-001 — Monolithe modulaire

**Accepté.** Django reste une application unique, séparée en modules métier.

## ADR-002 — Multi-tenant par `School`

**Accepté.** Les objets métier seront explicitement rattachés à un établissement. Pas de schéma PostgreSQL par école dans le MVP.

## ADR-003 — Tenant par sous-domaine

**Accepté.**

```text
slug.school.bewiseinnovation.com
```

Local :

```text
slug.localhost
```

## ADR-004 — `X-Tenant-Slug` uniquement en développement

**Accepté.** En production, la source de vérité sera le hostname.

## ADR-005 — SQLite local / PostgreSQL production

**Accepté.** Le projet local ne nécessite pas Docker.

## ADR-006 — User séparé de SchoolMembership

**Accepté.** Un utilisateur pourra appartenir à plusieurs écoles.

## ADR-007 — Les enseignants ne créent pas les séquences

**Accepté.** La direction crée année, période, séquence/examen. L'enseignant remplit uniquement les résultats autorisés.

## ADR-008 — Templates de bulletin contrôlés

**Accepté.** Plusieurs modèles seront proposés. L'école personnalisera logo, couleurs, informations, options d'affichage et signatures.

## ADR-009 — Bulletin publié = snapshot versionné

**Accepté.** Toute correction crée une nouvelle version officielle.

## ADR-010 — QR Code de vérification

**Accepté.** Chaque bulletin officiel aura un token non prédictible et une page de vérification en ligne.

## ADR-011 — WhatsApp à la demande

**Accepté.** Le parent initie la conversation. Le système identifie le parent puis répond avec les données auxquelles il a droit.


## ADR-011 — Une seule URL de portail affichée

**Statut : accepté**

L'interface ne stocke et n'affiche plus une URL locale et une URL production.

Le frontend calcule l'adresse du tenant depuis le domaine courant.

Exemples :

```text
localhost:5173
-> mon-ecole.localhost:5173
```

```text
prototype.bewiseinnovation.com
-> mon-ecole.prototype.bewiseinnovation.com
```

Le backend conserve uniquement le `slug` comme identité durable.

---

## ADR-012 — `SchoolDomain` réservé aux domaines personnalisés

**Statut : accepté**

Le wildcard principal n'exige pas de créer un `SchoolDomain` par école.

La résolution normale utilise :

```text
slug + BASE_DOMAIN
```

`SchoolDomain` servira plus tard pour des domaines personnalisés appartenant aux établissements.

---

## ADR-013 — Compte utilisateur != profil enseignant

**Statut : accepté**

L'étape 1 gère les comptes et leurs accès.

Les entités pédagogiques détaillées (`Teacher`, `Parent`, `Student`) seront créées dans `people` à l'étape 3.

Cela évite de mélanger authentification et données métier.


---

## ADR-014 — Les classes sont annuelles

**Statut : accepté**

Un `Level` décrit le niveau académique permanent :

```text
3e
CM2
Form 4
```

Une `Classroom` décrit un groupe réel pour une année :

```text
3e A — 2026/2027
```

Cela préserve correctement l'historique scolaire.

---

## ADR-015 — Hiérarchie Section → Cycle → Niveau

**Statut : accepté**

La structure est :

```text
School
→ Section
→ Cycle
→ Level
```

Cette hiérarchie permet notamment de représenter proprement un établissement bilingue avec des cursus francophone et anglophone distincts.

---

## ADR-016 — Une seule année scolaire active

**Statut : accepté**

Un établissement ne peut avoir qu'une seule `AcademicYear.is_active=True`.

L'activation d'une nouvelle année désactive automatiquement l'ancienne via l'API.

---

## ADR-017 — Générateur de structure = suggestion, pas règle métier

**Statut : accepté**

Le bouton de génération initialise une structure camerounaise courante selon la langue et les cycles de l'établissement.

Toutes les entités produites restent modifiables.

Le moteur ne doit jamais supposer qu'une école doit exactement suivre le template généré.


---

## ADR-018 — Access JWT court + refresh automatique

**Statut : accepté**

L'access token est volontairement court (15 minutes). Le client renouvelle automatiquement la session avec un refresh token valable 7 jours et rejoue la requête initiale.

Les endpoints de login ne doivent jamais déclencher une boucle de refresh.

---

## ADR-019 — Dictionnaires frontend FR / EN

**Statut : accepté**

Les nouvelles chaînes UI doivent être stockées dans :

```text
frontend/src/i18n/fr.js
frontend/src/i18n/en.js
```

Le mécanisme reste volontairement léger et sans dépendance i18n externe à ce stade.


---

## ADR-020 — Les périodes sont distinctes des séquences/examens

**Statut : accepté**

`AcademicPeriod` représente :

- trimestre ;
- semestre ;
- période personnalisée.

Les séquences, examens et compositions seront des objets séparés créés par la direction à l'intérieur d'une période.

---

## ADR-021 — Catalogue matière séparé du programme par niveau

**Statut : accepté**

Une `Subject` existe une seule fois dans l'établissement.

`LevelSubject` configure ensuite :

- le niveau ;
- le coefficient ;
- la langue ;
- la note maximale éventuelle.

Cela permet de réutiliser Mathématiques sur plusieurs niveaux sans dupliquer la matière.

---

## ADR-022 — Règle de passage par héritage

**Statut : accepté**

Ordre :

```text
Level override
→ Cycle override
→ AcademicPolicy établissement
```

La moyenne de passage n'est jamais codée en dur.

Le système de fin d'année utilisera cette règle pour proposer une décision, mais la direction gardera la validation finale.

---

## ADR-023 — Pas de loader plein écran après une mutation

**Statut : accepté**

Le loader principal ne doit apparaître qu'au chargement initial.

Les créations, suppressions et mises à jour doivent actualiser les données silencieusement afin de ne pas interrompre le travail de saisie.


---

## ADR-024 — Affectations matière/niveaux en bulk

**Statut : accepté**

Une matière peut être affectée à plusieurs niveaux dans une seule transaction.

L'API reçoit une liste de niveaux et applique la même configuration à chacun.

Pour une relation existante, le backend la met à jour plutôt que de créer un doublon.

---

## ADR-025 — Dialogues réutilisables pour l'édition

**Statut : accepté**

Les éditions rapides utilisent un composant `Dialog` commun au lieu de naviguer vers une autre page.

Premier usage :

- édition du catalogue matière ;
- édition d'une affectation matière/niveau.

Le même composant pourra être réutilisé pour les élèves, enseignants et évaluations.


---

## ADR-026 — Student permanent, Enrollment annuel

**Statut : accepté**

La fiche élève n'est pas copiée chaque année.

Chaque année scolaire crée une nouvelle `Enrollment`.

Cela permet les promotions et l'historique sans dupliquer l'identité de l'élève.

---

## ADR-027 — Teacher distinct de User

**Statut : accepté**

`Teacher` est un profil métier.

`User` est un compte d'authentification.

Un enseignant peut exister dans la base sans disposer immédiatement d'un accès à l'application.

---

## ADR-028 — Parent/enfant via table de relation

**Statut : accepté**

Une relation `StudentGuardian` porte :

- le type de relation ;
- le contact principal ;
- les droits de notification ;
- les droits de réception des résultats.

Un parent peut être lié à plusieurs enfants et un enfant à plusieurs responsables.

---

## ADR-029 — Décision de promotion stockée sur Enrollment

**Statut : accepté**

La moyenne finale et la décision concernent une année scolaire donnée.

Elles appartiennent donc à `Enrollment`, pas à `Student`.

Le moteur de résultats calculera plus tard la moyenne et proposera une décision.

La direction gardera la validation finale.

---

## ADR-030 — Données personnelles limitées aux rôles administratifs

**Statut : accepté**

Pour l'instant :

```text
OWNER / DIRECTOR / MANAGER
```

peuvent gérer élèves, enseignants, parents et inscriptions.

L'accès enseignant sera introduit plus tard avec un scope limité aux affectations pédagogiques.
