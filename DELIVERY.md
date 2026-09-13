# HOTFIX 06.2.1 — Prévisualisation PDF & notifications

Ce correctif s'applique par-dessus STEP 06.2.

## Corrigé

### 1. Onglet blanc pendant la prévisualisation

L'ancienne version ouvrait immédiatement une fenêtre vide avant que l'API
ait fini de générer le PDF. Selon le navigateur, `noopener` pouvait aussi
empêcher le code de récupérer la référence de cette fenêtre.

Désormais :

```text
clic Prévisualiser
→ chargement
→ PDF reçu
→ modale de prévisualisation dans l'application
```

Aucun onglet vide n'est créé.

Une fois le PDF disponible, l'utilisateur peut ensuite choisir :

```text
Télécharger
Ouvrir dans un nouvel onglet
Fermer
```

### 2. Notifications flottantes

Le module Bulletins appelle maintenant directement le système de toast
global introduit dans UI 07.3 :

- succès de publication ;
- aucune modification détectée ;
- publication classe ;
- ZIP téléchargé ;
- lien copié ;
- erreurs de chargement / prévisualisation / publication ;
- création, mise à jour et suppression des modèles A4.

Les anciens blocs verts/rouges dans la page ont été retirés.

## Installation locale

Extraire à la racine du projet en écrasant les fichiers :

```powershell
cd frontend
npm run dev
```

Aucune migration.
