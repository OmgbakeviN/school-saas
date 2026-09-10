# HOTFIX 03.2.2 — Routes export/import STEP 03.2

Le `404 Not Found` sur :

```text
/api/people/bulk/export/students/
/api/people/bulk/export/teachers/
/api/people/bulk/export/guardians/
/api/people/bulk/export/enrollments/
```

signifie que les URLs STEP 03.2 ne sont pas rattachées à
`apps.people.urls`.

Ce hotfix est autonome : il remet les fichiers backend STEP 03.2 et
ajoute de manière sûre :

```python
path("", include("apps.people.step_03_2_urls")),
```

dans `backend/apps/people/urls.py`.

## Installation

Extraire directement à la racine puis :

```powershell
python repair_step_03_2_export_routes.py
```

Ensuite :

```powershell
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
python manage.py check
python manage.py spectacular --validate --file openapi-schema.yml
python manage.py runserver 0.0.0.0:8000
```

Aucun `migrate` n'est nécessaire.
