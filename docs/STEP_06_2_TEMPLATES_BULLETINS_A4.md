# STEP 06.2 — Modèles de bulletins & moteur A4

## Objectif

Permettre à chaque établissement de choisir la présentation de ses bulletins
sans casser l'immutabilité des documents déjà publiés.

La chaîne devient :

```text
Résultats PUBLISHED
        ↓
Template actif pour le cycle
        ↓
Prévisualisation A4
        ↓
Validation : 1 seule feuille A4
        ↓
Publication
        ↓
ReportCardSnapshot immuable
```

## Modèles disponibles

### CLASSIC

```text
A4 portrait
```

Présentation administrative traditionnelle.

### MODERN

```text
A4 portrait
```

Branding plus visible, entête et synthèse davantage mis en valeur.

### COMPACT

```text
A4 portrait
```

Espacements et typographie plus denses. Recommandé quand un niveau possède
beaucoup de matières.

### SECONDARY_LANDSCAPE

```text
A4 paysage
```

Conçu pour les bulletins secondaires avec plusieurs colonnes et appréciations.

## Portée d'un modèle

Un modèle peut être :

```text
général à l'établissement
```

ou :

```text
spécifique à un Cycle
```

Résolution :

```text
1. modèle par défaut du Cycle
2. modèle général par défaut de l'établissement
3. premier modèle du Cycle
4. premier modèle général
5. fallback interne CLASSIC
```

Exemple :

```text
Établissement Primaire + Secondaire

Primaire
→ MODERN portrait

Secondaire
→ SECONDARY_LANDSCAPE
```

## Configuration

Chaque modèle peut contrôler :

```text
rang
moyenne de classe
effectif
décision annuelle
appréciations par matière
appréciation titulaire
appréciation direction
QR de vérification
échelle de police 80% à 110%
```

Le logo et les couleurs restent issus du branding de l'établissement.

## Version du modèle

`ReportCardTemplate.version` augmente lors d'une modification via l'API.

Au moment de la publication, le payload du bulletin contient une copie figée :

```json
{
  "template": {
    "id": 2,
    "name": "Secondaire officiel",
    "key": "SECONDARY_LANDSCAPE",
    "version": 3,
    "orientation": "LANDSCAPE",
    "font_scale": "0.95",
    "options": {
      "show_rank": true,
      "show_class_average": true,
      "show_qr": true
    }
  }
}
```

Ainsi une modification ultérieure du modèle ne transforme jamais les anciens
bulletins.

## Garantie une feuille A4

Le moteur PDF rend d'abord le document avec la configuration choisie.

Si le PDF produit plus d'une page, il tente automatiquement plusieurs niveaux
de compactage :

```text
configuration demandée
        ↓
espacements plus denses
        ↓
échelle légèrement réduite
        ↓
mode compact de secours
```

La taille de secours ne descend pas sous une limite contrôlée.

Si le document dépasse encore une feuille :

```text
publication refusée
```

avec une recommandation :

```text
utiliser COMPACT
ou SECONDARY_LANDSCAPE
ou masquer certaines colonnes
ou réduire l'échelle de police
```

Un bulletin officiel multi-page ne peut donc pas être publié par accident.

## Prévisualisation

Depuis :

```text
Bulletins
→ Explorateur
→ ouvrir un élève
→ Prévisualiser PDF A4
```

le backend génère un PDF temporaire.

Ce document porte la mention :

```text
APERÇU - DOCUMENT NON OFFICIEL
```

et ne crée aucun `ReportCardSnapshot`.

Headers utiles :

```text
X-Report-Card-Pages
X-Report-Card-Fits-A4
X-Report-Card-Template
X-Report-Card-Orientation
```

## Publication intelligente

Le template fait maintenant partie du contenu significatif du bulletin.

Donc :

```text
v1 CLASSIC
↓ aucun changement
v1 conservée
```

mais :

```text
v1 CLASSIC
↓ modèle changé vers MODERN
v2 créée
```

La métadonnée technique de rendu (`render`) n'est pas utilisée pour décider
s'il faut une nouvelle version.

## Permissions

### OWNER / DIRECTOR

- créer un modèle ;
- modifier ;
- supprimer ;
- définir par défaut ;
- prévisualiser ;
- publier.

### MANAGER / TEACHER

Le comportement existant de consultation reste inchangé.

La configuration des modèles est réservée à la direction.
