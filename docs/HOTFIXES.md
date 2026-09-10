# Hotfixes

## HOTFIX 01.1 — Formulaire d'installation : perte de focus

### Symptôme

À chaque caractère saisi dans un champ du formulaire de création d'établissement, le champ perdait le focus. Il fallait recliquer avant de saisir le caractère suivant.

### Cause

`Field` était déclaré à l'intérieur de `CreateSchoolPage` :

```jsx
const Field = (...) => ...
```

À chaque changement de state, `CreateSchoolPage` était rendu à nouveau et une nouvelle identité de composant `Field` était créée. React démontait puis remontait les champs enfants, ce qui supprimait le focus.

### Correction

Le composant a été déplacé vers :

```text
frontend/src/components/Field.jsx
```

Il possède maintenant une identité stable entre les rendus.

### Impact

Aucune migration backend. Aucun changement d'API. Il suffit de remplacer les fichiers du frontend contenus dans le ZIP de correctif.
