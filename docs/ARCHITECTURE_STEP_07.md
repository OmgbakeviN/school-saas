# Architecture — STEP 07 Finance

## Application

```text
apps.finance
```

Dépendances :

```text
tenants
accounts
academics
people
```

Le module Finance ne dépend pas de `assessments` ni de `report_cards`.

## Entités

```text
TuitionPlan
TuitionInstallment
StudentTuitionAccount
TuitionPayment
PaymentAllocation
PaymentReceiptSnapshot
```

## Multi-tenancy

Toutes les entités opérationnelles stockent ou dérivent `school`.

Tous les endpoints privés filtrent avec :

```text
request.school
```

Un paiement d'un autre établissement ne peut donc pas être résolu depuis le
tenant courant.

## Historique annuel

La clé métier centrale est :

```text
StudentTuitionAccount.enrollment
```

et `Enrollment` est déjà unique par :

```text
school + student + academic_year
```

Cela garantit la séparation financière annuelle.

## Reçu snapshot

Le PDF est généré au moment du paiement.

`PaymentReceiptSnapshot` stocke :

```text
payload
payload_sha256
pdf_file
pdf_sha256
```

Le téléchargement ne reconstruit pas le reçu à partir de données qui auraient
pu évoluer.

## Allocation

`PaymentAllocation` matérialise la répartition entre paiement et tranches.

Cela permet plus tard de répondre précisément :

```text
1ère tranche soldée ?
2ème tranche payée à combien ?
quelle échéance reste ouverte ?
```
