# BE WISE School SaaS — STEP 03.1

Cette livraison ajoute la gestion des personnes et des inscriptions annuelles.

## Nouveautés

- élèves ;
- enseignants ;
- parents / tuteurs ;
- liens parent ↔ élève ;
- contact principal ;
- autorisation de recevoir les résultats ;
- inscriptions annuelles ;
- historique par année ;
- préparation des décisions de fin d'année ;
- dashboard avec vrais comptes élèves/enseignants ;
- FR / EN ;
- tests multi-tenant.

## Installation

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd backend
python manage.py migrate
python manage.py test apps.accounts apps.tenants apps.academics apps.people
python manage.py runserver 0.0.0.0:8000
```

Frontend :

```powershell
cd frontend
npm install
npm run dev
```

## Migration

```text
people.0001_initial
```

## Utilisation

Dans le menu :

```text
Personnes & inscriptions
```

Ordre conseillé :

1. créer les élèves ;
2. créer les enseignants ;
3. créer les parents/tuteurs ;
4. lier les parents aux élèves ;
5. inscrire les élèves dans leurs classes pour l'année active.

## Historique

Exemple :

```text
Paul Omgba
2026/2027 → 3e A
2027/2028 → 2nde A
2028/2029 → 1ère B
```

La même fiche élève est conservée.

La prochaine étape est :

**STEP 03.2 — Imports, affectation massive et promotion de fin d'année.**


## Swagger / OpenAPI

```text
/api/docs/   Swagger UI
/api/redoc/  ReDoc
/api/schema/ OpenAPI
```

Validation :

```powershell
cd backend
python manage.py spectacular --validate --file openapi-schema.yml
```


## STEP 03.2 — Opérations de masse

Dans `Personnes & inscriptions > Opérations` : imports CSV/XLSX, affectation massive, fin d'année, nouvelle année et exports.

```powershell
python apply_step_03_2.py
pip install -r backend\\requirements.txt
cd backend
python manage.py spectacular --validate --file openapi-schema.yml
python manage.py test apps.accounts apps.tenants apps.academics apps.people
```
