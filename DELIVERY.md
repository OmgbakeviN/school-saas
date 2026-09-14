# BE WISE School — STEP 07.4.1
## Drill-down des statistiques par classe

Cette livraison s'applique par-dessus STEP 07.4 Dashboard Statistics.

## Installation locale

Extraire le ZIP à la racine du projet en écrasant les fichiers.

Backend :

```powershell
cd backend
python manage.py check
python manage.py test apps.tenants
python manage.py runserver 0.0.0.0:8000
```

Frontend :

```powershell
cd frontend
npm run dev
```

## Test fonctionnel

```text
Tableau de bord
→ Effectifs par classe
→ cliquer sur une classe
```

Vérifier :

```text
population
répartition filles / garçons
équipe pédagogique
matières
évaluations et taux de publication
moyennes par matière
bulletins publiés
décisions annuelles
pension de la classe (si le rôle y a accès)
```

Tester également avec un compte enseignant :

```text
classe affectée → accès OK
classe non affectée → accès refusé
```

## Migration

Aucune.

## Validation de génération

- syntaxe Python vérifiée ;
- syntaxe FR/EN vérifiée ;
- JSX vérifié ;
- route explicite vérifiée ;
- tests Django ajoutés.

Les tests Django runtime doivent être exécutés sur l'environnement local du
projet.
