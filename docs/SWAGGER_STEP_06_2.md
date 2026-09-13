# Swagger — STEP 06.2

## Modèles

```http
GET /api/report-cards/templates/
POST /api/report-cards/templates/
```

Exemple création :

```json
{
  "name": "Bulletin secondaire officiel",
  "cycle": 4,
  "template_key": "SECONDARY_LANDSCAPE",
  "is_default": true,
  "show_rank": true,
  "show_class_average": true,
  "show_effective": true,
  "show_decision": true,
  "show_subject_comments": true,
  "show_teacher_comment": true,
  "show_direction_comment": true,
  "show_qr": true,
  "font_scale": "0.95"
}
```

## Détail

```http
GET /api/report-cards/templates/{id}/
PATCH /api/report-cards/templates/{id}/
DELETE /api/report-cards/templates/{id}/
```

## Définir par défaut

```http
POST /api/report-cards/templates/{id}/set-default/
```

```json
{
  "is_default": true
}
```

## Prévisualisation PDF

```http
POST /api/report-cards/preview/
```

Même payload principal qu'une publication :

```json
{
  "enrollment": 21,
  "report_type": "PERIOD",
  "academic_period": 4,
  "teacher_comment": "",
  "general_comment": "",
  "subject_comments": {}
}
```

Optionnellement :

```json
{
  "template": 3
}
```

pour tester explicitement un modèle appartenant au même établissement.

Réponse réussie :

```text
200 application/pdf
```

Le PDF porte la mention non officielle et aucun snapshot n'est créé.

Si le document ne tient pas sur une feuille A4 :

```text
409
```

avec une explication.
