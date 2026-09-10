# HOTFIX 03.1.1 — Générateur de données de démonstration

Cette livraison ajoute une commande Django permettant de remplir un établissement existant avec des données fictives cohérentes.

## Ce qui est généré

- élèves ;
- inscriptions dans les classes de l'année active ;
- enseignants ;
- parents/tuteurs ;
- familles avec quelques frères/sœurs ;
- liens parent ↔ enfant ;
- contact principal ;
- téléphones fictifs ;
- spécialités d'enseignants basées sur les matières déjà configurées.

La structure académique existante n'est jamais recréée ni modifiée.

## Utilisation

Si la base ne contient qu'un établissement :

```powershell
python manage.py seed_school_demo
```

S'il y a plusieurs établissements :

```powershell
python manage.py seed_school_demo --school mon-ecole
```

Volume personnalisé :

```powershell
python manage.py seed_school_demo --school mon-ecole --students 200 --teachers 30 --guardians 150
```

Repartir de zéro pour les données de démonstration uniquement :

```powershell
python manage.py seed_school_demo --school mon-ecole --reset
```

Supprimer uniquement les données de démonstration :

```powershell
python manage.py seed_school_demo --school mon-ecole --clear
```

## Sécurité du nettoyage

Les élèves générés utilisent :

```text
DEMO-STU-xxxxx
```

Les enseignants :

```text
DEMO-TCH-xxxxx
```

Les parents/tuteurs utilisent le domaine fictif :

```text
@demo.bewise.local
```

`--clear` cible uniquement ces données.

## Migration

Aucune migration.
