# Swagger / OpenAPI — BE WISE School

La documentation API utilise **drf-spectacular**.

## URLs

```text
Swagger UI : http://127.0.0.1:8000/api/docs/
ReDoc      : http://127.0.0.1:8000/api/redoc/
Schema     : http://127.0.0.1:8000/api/schema/
```

Sur localhost, les routes tenant peuvent utiliser :

```text
X-Tenant-Slug: mon-ecole
```

Le bouton **Authorize** permet d'utiliser le JWT Bearer.

## Générer le schéma

```powershell
python manage.py spectacular --file openapi-schema.yml
python manage.py spectacular --validate --file openapi-schema.yml
```

Pour les futurs endpoints métier complexes de STEP 03.2, utiliser
`drf_spectacular.utils.extend_schema` avec des serializers de request/response.


## STEP 03.2 — endpoints

```text
POST /api/people/bulk/import/{entity}/
GET  /api/people/bulk/import-template/{entity}/
POST /api/people/bulk/class-assignment/
POST /api/people/promotion/preview/
POST /api/people/promotion/apply/
POST /api/people/promotion/re-enroll-repeaters/
POST /api/people/promotion/exit/
POST /api/people/academic-years/prepare/
GET  /api/people/bulk/export/{entity}/
```
