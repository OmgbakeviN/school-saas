# HOTFIX 07.1 — Formulaire de paiement responsive

Extraire directement à la racine du projet en écrasant les fichiers.

```text
C:\Users\dell\school saas
```

Aucun changement backend et aucune migration.

Le modal de paiement utilise maintenant :

```text
hauteur max = viewport
header fixe
contenu scrollable
footer fixe
```

Ainsi, même avec plusieurs tranches, les boutons de validation restent
toujours accessibles.

Redémarrer Vite si nécessaire :

```powershell
cd frontend
npm run dev
```
