# STEP 07 — Gestion de la pension & reçus

## Objectif

Gérer les frais scolaires annuels d'un élève à partir de son `Enrollment`.

La chaîne est :

```text
AcademicYear
   ↓
TuitionPlan
   ↓
TuitionInstallment
   ↓
StudentTuitionAccount
   ↓
TuitionPayment
   ↓
PaymentAllocation
   ↓
PaymentReceiptSnapshot
   ↓
PDF reçu officiel
```

## Plan de pension

Un plan appartient à une année scolaire.

Il peut viser :

```text
un niveau
ou
une classe
ou
tous les élèves de l'année
```

Exemple :

```text
Pension Class 6 — 2026/2027
```

## Tranches

Chaque plan peut être découpé en plusieurs échéances :

```text
1ère tranche     50 000 FCFA
2ème tranche     40 000 FCFA
3ème tranche     30 000 FCFA
```

Chaque tranche possède :

- un nom ;
- un montant ;
- une date d'échéance optionnelle ;
- un ordre.

La pension totale correspond à la somme des tranches actives.

## Comptes élèves

Un `StudentTuitionAccount` est lié à une `Enrollment`.

Cela signifie qu'un élève garde son historique d'une année à l'autre :

```text
Student
 ├── Enrollment 2026/2027
 │      └── TuitionAccount 2026/2027
 │
 └── Enrollment 2027/2028
        └── TuitionAccount 2027/2028
```

On ne mélange donc jamais les paiements de deux années scolaires.

## Affectation massive

Après création du plan et des tranches :

```text
Créer / synchroniser les comptes élèves
```

Le backend crée automatiquement un compte pour tous les élèves éligibles.

Si le plan vise un niveau, il prend toutes les classes de ce niveau pour
l'année choisie.

Si un élève a déjà un autre plan sans paiement, le plan peut être synchronisé.

S'il existe déjà des paiements, le système signale un conflit au lieu de
changer silencieusement la pension.

## Paiement

Un paiement contient :

```text
élève / compte pension
montant
date
mode
référence
notes
utilisateur ayant encaissé
numéro de reçu
```

Modes prévus :

```text
CASH
MOBILE_MONEY
BANK_TRANSFER
CARD
OTHER
```

## Imputation automatique

Le paiement est automatiquement imputé aux tranches les plus anciennes encore
non soldées.

Exemple :

```text
1ère tranche : 50 000
2ème tranche : 40 000

paiement : 60 000
```

donne :

```text
1ère tranche : 50 000 payés
2ème tranche : 10 000 payés
```

## Contrôle du trop-perçu

STEP 07 refuse un paiement supérieur au solde restant.

Exemple :

```text
reste à payer : 30 000
paiement saisi : 40 000
```

→ refus.

La gestion des avoirs / remboursements / crédits pourra être ajoutée dans une
étape finance avancée.

## Statuts

Le compte calcule automatiquement :

```text
UNPAID   → aucun paiement
PARTIAL  → paiement partiel
PAID     → pension soldée
```

## Tableau de bord

Le tableau de bord affiche :

- pension totale attendue ;
- total encaissé ;
- reste à encaisser ;
- taux de recouvrement ;
- encaissements du jour ;
- nombre d'élèves soldés ;
- nombre de paiements partiels ;
- nombre d'impayés.

Filtres :

```text
année scolaire
classe
```

## Reçu PDF

Chaque paiement génère immédiatement un PDF officiel.

Le reçu contient :

- branding de l'établissement ;
- numéro unique ;
- date ;
- élève ;
- matricule ;
- classe ;
- année ;
- plan de pension ;
- montant payé ;
- moyen de paiement ;
- référence ;
- détail des tranches imputées ;
- pension totale ;
- total payé après ce paiement ;
- reste à payer ;
- utilisateur ayant encaissé ;
- zone cachet / signature ;
- empreinte courte du reçu.

Le numéro prend la forme :

```text
REC-2026-0000123
```

Le dernier bloc numérique provient de l'identifiant immuable du paiement.

## Immutabilité financière

Un paiement enregistré n'est pas modifiable via l'API.

Le reçu est lui aussi immuable.

Le Django Admin est configuré en lecture seule pour :

```text
TuitionPayment
PaymentReceiptSnapshot
```

Cette décision évite de transformer silencieusement l'historique de caisse.

## Verrouillage du plan

Dès qu'un premier paiement utilise un plan :

```text
montants des tranches
ordre
année
niveau / classe
devise
```

ne doivent plus être modifiés.

L'établissement peut désactiver le plan ou en créer un nouveau si nécessaire.

## Permissions

### OWNER / DIRECTOR / MANAGER

- tableau de bord ;
- configuration des plans ;
- configuration des tranches ;
- création des comptes élèves ;
- encaissements ;
- reçus.

### ACCOUNTANT

- tableau de bord ;
- comptes élèves ;
- encaissements ;
- historique ;
- reçus.

Il ne configure pas les plans.

### TEACHER

Aucun accès au module financier.

## Limites volontaires de STEP 07

Non inclus pour le moment :

- remises / bourses ;
- remboursements ;
- annulation comptable ;
- avoirs ;
- relances WhatsApp ;
- frais annexes (transport, cantine, uniforme, etc.) séparés de la pension ;
- export comptable avancé.

Le modèle est néanmoins conçu pour pouvoir évoluer vers ces fonctions.
