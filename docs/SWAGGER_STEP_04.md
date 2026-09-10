# Swagger — STEP 04

Après migration et démarrage du backend :

```text
http://127.0.0.1:8000/api/docs/
```

Les nouvelles routes apparaissent sous le tag `Teaching`.

## Affectations

```text
GET    /api/teaching/assignments/
POST   /api/teaching/assignments/
GET    /api/teaching/assignments/{id}/
PATCH  /api/teaching/assignments/{id}/
DELETE /api/teaching/assignments/{id}/
```

## Titulaire / professeur principal

```text
GET    /api/teaching/leaderships/
POST   /api/teaching/leaderships/
GET    /api/teaching/leaderships/{id}/
PATCH  /api/teaching/leaderships/{id}/
DELETE /api/teaching/leaderships/{id}/
```

## Espace enseignant

```text
GET /api/teaching/me/
```

## Compte enseignant

```text
POST   /api/teaching/teachers/{teacher_id}/account/
DELETE /api/teaching/teachers/{teacher_id}/account/
```

## Mot de passe personnel

```text
POST /api/auth/change-password/
```

## Validation du schéma

```powershell
python manage.py spectacular --validate --file openapi-schema.yml
```

En local, Swagger continue d'utiliser :

```text
X-Tenant-Slug
```

pour choisir l'établissement.
