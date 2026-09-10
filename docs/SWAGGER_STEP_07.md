# Swagger — STEP 07 Finance

## Groupe

```text
Finance
```

## Options

```http
GET /api/finance/options/
```

## Tableau de bord

```http
GET /api/finance/dashboard/
```

Filtres :

```text
academic_year
classroom
```

## Plans

```http
GET  /api/finance/plans/
POST /api/finance/plans/
GET  /api/finance/plans/{id}/
PATCH /api/finance/plans/{id}/
DELETE /api/finance/plans/{id}/
```

## Tranches

```http
GET  /api/finance/plans/{plan_id}/installments/
POST /api/finance/plans/{plan_id}/installments/
PATCH /api/finance/installments/{id}/
DELETE /api/finance/installments/{id}/
```

## Créer les comptes élèves

```http
POST /api/finance/plans/{plan_id}/assign/
```

## Comptes pension

```http
GET /api/finance/accounts/
GET /api/finance/accounts/{account_id}/
```

Filtres :

```text
academic_year
classroom
payment_status
search
```

## Paiements

```http
GET  /api/finance/payments/
POST /api/finance/payments/record/
```

Exemple :

```json
{
  "tuition_account": 12,
  "amount": "50000.00",
  "method": "MOBILE_MONEY",
  "reference": "OM-98382727",
  "notes": ""
}
```

## Reçu PDF

```http
GET /api/finance/payments/{payment_id}/receipt/
```

Réponse :

```text
application/pdf
```
