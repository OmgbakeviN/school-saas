# UI 07.2 — Thème dynamique & responsive mobile

## Objectif

Le portail d'un établissement doit reprendre automatiquement son identité visuelle :

```text
School.primary_color
School.secondary_color
School.logo
School.motto
```

La même interface doit rester confortable sur téléphone, tablette et desktop.

## Couleurs

Le portail définit des variables CSS par tenant :

```text
--school-primary
--school-primary-rgb
--school-secondary
--school-secondary-rgb
--school-on-primary
--school-on-secondary
```

Les actions principales déjà écrites avec `bg-slate-950` sont remappées à la couleur principale uniquement à l'intérieur de `.tenant-theme`.

Cela permet aux modules existants — Académique, Personnes, Évaluations, Bulletins, Finance — de reprendre la couleur de l'établissement sans réécrire chacun de leurs boutons.

La couleur secondaire est utilisée dans la barre de signature visuelle du portail.

## Contraste

Le frontend calcule automatiquement si le texte posé sur la couleur principale doit être blanc ou noir.

Une école peut donc utiliser une couleur principale claire sans rendre les boutons illisibles.

## Écran de connexion

`App.jsx` transmet désormais le contexte public de l'école à `TenantPortal`.

Le portail peut donc afficher avant connexion :

- logo ;
- nom ;
- devise ;
- couleur principale ;
- couleur secondaire.

## Logo

`SchoolIdentity` :

- utilise `object-contain` plutôt que `object-cover` ;
- garde le logo entier ;
- affiche un pictogramme de secours si le fichier image échoue.

## Mobile

Sous `lg`, la sidebar n'est plus affichée au-dessus de tout le contenu.

Elle devient un drawer :

```text
[☰] Header
  ↓
menu latéral mobile
```

Le drawer :

- se ferme après sélection d'un module ;
- se ferme en cliquant sur l'overlay ;
- se ferme avec la touche `Escape` ;
- bloque le scroll du contenu derrière ;
- possède son propre scroll vertical.

## Formulaires et tableaux

Sur mobile :

- les champs passent au minimum à 16px pour éviter le zoom automatique iOS ;
- les conteneurs `overflow-x-auto` conservent un scroll tactile fluide ;
- les gros rayons sont légèrement réduits ;
- le dashboard utilise des espacements plus compacts.

## Changement de couleur en direct

Quand OWNER/DIRECTOR modifie les couleurs dans `Établissement`, `SchoolSettingsPanel` renvoie l'école mise à jour au `TenantPortal`.

Les variables CSS sont recalculées immédiatement : aucun rechargement du navigateur n'est nécessaire.
