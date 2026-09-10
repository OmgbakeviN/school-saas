# Swagger — STEP 05

Swagger UI :

```text
/api/docs/
```

Endpoints :

```text
GET   /api/assessments/period-controls/
PATCH /api/assessments/period-controls/{period_id}/

GET   /api/assessments/assessments/
POST  /api/assessments/assessments/
GET   /api/assessments/assessments/{id}/
PATCH /api/assessments/assessments/{id}/
DELETE /api/assessments/assessments/{id}/

GET   /api/assessments/assessments/{id}/gradebook/
PUT   /api/assessments/assessments/{id}/gradebook/

POST  /api/assessments/assessments/{id}/open/
POST  /api/assessments/assessments/{id}/submit/
POST  /api/assessments/assessments/{id}/validate/
POST  /api/assessments/assessments/{id}/publish/
POST  /api/assessments/assessments/{id}/reopen/

GET   /api/assessments/results/classrooms/{classroom_id}/periods/{period_id}/
POST  /api/assessments/years/{year_id}/recalculate-averages/
```

En développement local, Swagger peut utiliser :

```text
X-Tenant-Slug: bws
```

et l'authentification JWT Bearer existante.

## STEP 05.1

Aucun nouvel endpoint n'est nécessaire.

`/api/teaching/assignments/` et `/api/teaching/me/` exposent maintenant :

```json
{
  "source": "CLASS_TEACHER_AUTO",
  "source_label": "Générée depuis le titulaire de classe",
  "is_automatic": true
}
```

Les endpoints d'évaluation continuent à recevoir un
`teaching_assignment` entier.

