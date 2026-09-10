# HOTFIX 03.2.1 — Réparation imports Swagger

Le patch STEP 03.2 pouvait insérer les imports `drf_spectacular`
au milieu d'un import Python multi-ligne et provoquer :

```text
SyntaxError: unmatched ')'
```

Ce hotfix répare les fichiers affectés et sécurise le script d'installation.

## Utilisation

```powershell
python repair_step_03_2_swagger_imports.py

cd backend
python manage.py check
python manage.py spectacular --validate --file openapi-schema.yml
python manage.py runserver 0.0.0.0:8000
```

Aucune migration.
