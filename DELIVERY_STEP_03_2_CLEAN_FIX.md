# STEP 03.2 — Clean Export Fix

Cette livraison a été reconstruite à partir des fichiers `backend.zip` et
`src.zip` fournis par le développeur.

Il n'y a **aucun script de patch** à exécuter.

## Ce qui a été changé

Les opérations STEP 03.2 ont été refactorées vers une architecture Django
explicite :

```text
backend/apps/people/operations_serializers.py
backend/apps/people/operations_services.py
backend/apps/people/operations_views.py
backend/apps/people/urls.py
```

Les anciens fichiers `step_03_2_*` ne sont plus utilisés.

Les routes d'export sont maintenant déclarées directement dans
`apps/people/urls.py` :

```text
GET /api/people/exports/students/
GET /api/people/exports/teachers/
GET /api/people/exports/guardians/
GET /api/people/exports/enrollments/
```

Formats :

```text
?format=xlsx
?format=csv
```

Filtres possibles pour élèves / inscriptions :

```text
?academic_year=<id>
?classroom=<id>
```

## Imports

```text
POST /api/people/imports/students/
POST /api/people/imports/teachers/
POST /api/people/imports/guardians/
```

Modèles CSV :

```text
GET /api/people/imports/templates/students/
GET /api/people/imports/templates/teachers/
GET /api/people/imports/templates/guardians/
```

## Installation

1. Arrêter complètement `runserver`.
2. Extraire ce ZIP à la racine du projet en écrasant les fichiers existants.
3. Ne pas supprimer votre `.env`, votre `db.sqlite3` ou vos médias :
   ils ne sont volontairement pas inclus dans cette archive.
4. Relancer :

```powershell
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
python manage.py check
python manage.py spectacular --validate --file openapi-schema.yml
python manage.py test apps.people.tests.test_step_03_2_operations
python manage.py runserver 0.0.0.0:8000
```

Frontend :

```powershell
cd frontend
npm run dev
```

## Test direct

Après connexion au tenant, ces URLs doivent répondre 200 :

```text
/api/people/exports/students/?format=xlsx
/api/people/exports/teachers/?format=xlsx
/api/people/exports/guardians/?format=xlsx
/api/people/exports/enrollments/?format=xlsx
```

## Migration

Aucune migration.
