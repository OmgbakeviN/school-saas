# HOTFIX 03.1.2 — Swagger / OpenAPI

Ajoute drf-spectacular au projet BE WISE School.

## Installation

Extraire à la racine puis :

```powershell
python apply_hotfix_03_1_2_swagger.py

.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
python manage.py spectacular --validate --file openapi-schema.yml
python manage.py runserver 0.0.0.0:8000
```

Ouvrir :

```text
http://127.0.0.1:8000/api/docs/
```

Aucune migration.
