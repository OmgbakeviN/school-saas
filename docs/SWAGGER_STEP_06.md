# Swagger — STEP 06

## Groupe

```text
Report Cards
```

## Options

```http
GET /api/report-cards/options/
```

## Résultats par classe / période

```http
GET /api/report-cards/results/classrooms/{classroom_id}/periods/{period_id}/
```

## Résultat individuel / période

```http
GET /api/report-cards/results/students/{enrollment_id}/periods/{period_id}/
```

## Résultats d'une matière

```http
GET /api/report-cards/results/subjects/{subject_id}/periods/{period_id}/?classroom=12
```

## Résultats annuels d'une classe

```http
GET /api/report-cards/results/classrooms/{classroom_id}/annual/
```

## Résultat annuel individuel

```http
GET /api/report-cards/results/students/{enrollment_id}/annual/
```

## Bulletins publiés

```http
GET /api/report-cards/snapshots/
```

Filtres :

```text
academic_year
period
classroom
student
report_type
latest_only
```

## Publication individuelle

```http
POST /api/report-cards/publish/
```

Exemple :

```json
{
  "enrollment": 21,
  "report_type": "PERIOD",
  "academic_period": 4,
  "teacher_comment": "Bon trimestre.",
  "general_comment": "Encouragements.",
  "subject_comments": {
    "2": "Très bon travail en mathématiques."
  }
}
```

## Publication massive

```http
POST /api/report-cards/publish/classroom/
```

```json
{
  "classroom": 7,
  "report_type": "PERIOD",
  "academic_period": 4
}
```

## PDF

```http
GET /api/report-cards/snapshots/{snapshot_id}/pdf/
```

Réponse :

```text
application/pdf
```

## Vérification publique API

```http
GET /api/public/report-cards/verify/{token}/
```

Aucune authentification.

## Page publique

```text
/verify/report-card/{token}/
```


## STEP 06.1 — ZIP d'une classe

```http
GET /api/report-cards/download/classroom-zip/
```

Query parameters :

```text
classroom
report_type
academic_period
```

Réponse :

```text
application/zip
```

Headers utiles :

```text
X-Report-Cards-Included
X-Report-Cards-Missing
```

## STEP 06.1 — Publication sans changement

`POST /api/report-cards/publish/` renvoie maintenant :

```json
{
  "snapshot": {
    "id": 12,
    "version": 1
  },
  "created_new_version": false,
  "unchanged": true
}
```

HTTP `200` signifie qu'aucune nouvelle version n'était nécessaire.

HTTP `201` signifie qu'une nouvelle version officielle a été créée.
