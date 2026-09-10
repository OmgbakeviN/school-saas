# STEP 06.1 — Améliorations bulletins

## 1. Classement dense

La règle de classement devient :

```text
moyennes : 15, 15, 13, 12
rangs    :  1,  1,  2,  3
```

Deux élèves ayant exactement la même moyenne ont le même rang.

Le rang suivant est le prochain rang distinct, et non la position physique
dans la liste.

Cette règle s'applique :

- au classement général d'une période ;
- au classement annuel ;
- au classement d'une matière.

## 2. Signification de la décision "En attente"

`Enrollment.promotion_decision = PENDING` signifie que la direction n'a pas
encore arrêté la décision de fin d'année.

Ce n'est pas une erreur et ce n'est pas une décision automatique.

Dans les nouveaux bulletins, le texte affiché devient :

```text
Décision de fin d'année non arrêtée
```

Une fois la décision validée dans le workflow de promotion, le bulletin
annuel affiche par exemple :

```text
Admis / promu
Redouble
Diplômé
Transféré
Retiré
```

## 3. Publication uniquement en cas de modification

Avant STEP 06.1, cliquer deux fois sur `Publier` produisait :

```text
v1
v2
```

même si rien n'avait changé.

Désormais le backend calcule une empreinte du contenu significatif du
bulletin en ignorant uniquement les métadonnées de publication :

```text
version
published_at
verification token / fingerprint
```

Si les notes, rangs, appréciations, branding, décision, titulaire, etc.
sont identiques :

```text
v1
↓ nouvelle tentative
v1 conservée
```

Si le contenu change :

```text
v1
↓ modification
v2
```

La publication massive suit la même règle.

## 4. ZIP de toute une classe

Nouvel endpoint :

```http
GET /api/report-cards/download/classroom-zip/
```

Paramètres :

```text
classroom
report_type = PERIOD | ANNUAL
academic_period  # obligatoire pour PERIOD
```

Exemple :

```text
/api/report-cards/download/classroom-zip/
  ?classroom=7
  &report_type=PERIOD
  &academic_period=4
```

Le ZIP contient la **dernière version publiée** de chaque élève.

Il contient également :

```text
manifest.txt
```

qui indique :

- le nombre de bulletins inclus ;
- le nombre d'élèves sans bulletin publié ;
- la liste des élèves manquants, le cas échéant.

Le téléchargement ne publie jamais automatiquement un bulletin.

Il télécharge uniquement les documents officiels déjà publiés.

## 5. Interface

Dans l'explorateur de bulletins, quand une classe et un contexte sont
sélectionnés :

```text
[Publier toute la classe]
[Télécharger les bulletins ZIP]
```

Le bouton ZIP est également disponible pour un titulaire / professeur
principal ayant accès au bulletin complet de la classe.

## Migration

Aucune migration.
