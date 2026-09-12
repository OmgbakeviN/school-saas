# UI 07.3 — Thème immersif & notifications flottantes

## Objectif

Renforcer visuellement l'identité de chaque établissement sans créer un thème
spécifique à la main pour chaque école.

Les couleurs enregistrées dans `School.primary_color` et
`School.secondary_color` pilotent maintenant davantage l'interface :

- fonds ambiants ;
- gradients ;
- navigation active ;
- boutons principaux ;
- cartes ;
- focus des champs ;
- header ;
- menu latéral ;
- login du tenant ;
- notifications d'information.

## Gradients dynamiques

Le thème construit un gradient à partir de :

```text
primary_color
+
secondary_color
```

Les couleurs ne sont pas codées en dur dans les modules métier.

Exemple :

```text
primary_color   = #144dd2
secondary_color = #0a0a0b
```

produit automatiquement des accents bleu / noir, tout en conservant les zones
de saisie et les tableaux suffisamment clairs.

## Notifications flottantes

Un composant global `FloatingNotifications` affiche maintenant les retours de
formulaire sous forme de toasts en haut à droite sur desktop et en haut de
l'écran sur mobile.

Types disponibles :

```text
success
error
warning
info
```

API pour les nouveaux développements :

```js
import {
  notifySuccess,
  notifyError,
  notifyInfo,
  notifyWarning,
} from "../lib/toast";

notifySuccess("Établissement enregistré.");
notifyError("Impossible d'enregistrer le paiement.");
```

## Compatibilité avec les écrans existants

Les modules actuels utilisent encore souvent des blocs inline comme :

```text
bg-emerald-50 + text-emerald-*
bg-rose-50 + text-rose-*
```

`FloatingNotifications` contient un pont de compatibilité : il détecte les
boîtes de succès/erreur existantes, les transforme en notifications flottantes
et masque le bloc inline correspondant.

Cela permet d'améliorer immédiatement les formulaires déjà développés sans
réécrire chaque module.

Les badges de statut `Soldé`, `Impayé`, etc. ne sont pas convertis, car les
badges `rounded-full` sont explicitement ignorés.

## Accessibilité

- `aria-live="polite"` pour les messages normaux ;
- `role="alert"` pour les erreurs ;
- bouton de fermeture ;
- durée d'affichage automatique ;
- `prefers-reduced-motion` respecté ;
- contraste des boutons conservé via le calcul déjà présent dans
  `schoolTheme.js`.

## Responsive

Les notifications prennent presque toute la largeur disponible sur mobile et
une largeur maximale d'environ 390 px sur desktop.

Le responsive introduit en UI 07.2 est conservé : drawer mobile, header sticky,
scroll horizontal des tableaux et contrôles tactiles.
