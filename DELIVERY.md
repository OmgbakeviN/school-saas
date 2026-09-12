# HOTFIX 07.3.1 — Menu hamburger mobile

Ce correctif s'applique par-dessus UI 07.3.

## Problème corrigé

La règle immersive UI 07.3 appliquait `position: relative` à tous les
enfants directs du portail. Elle écrasait donc les classes Tailwind
`fixed` et `sticky`.

Sur mobile, le menu hamburger était alors rendu dans le flux normal de la
page au lieu d'être un drawer plein écran.

## Correction

- overlay réellement `fixed`
- backdrop plein écran
- drawer `100dvh`
- header du portail à nouveau sticky
- contenu du drawer scrollable
- identité école compacte
- fallback `100vh`

## Installation

Extraire ce ZIP à la racine du projet en écrasant les fichiers.

```powershell
cd frontend
npm run dev
```

Aucune migration.
