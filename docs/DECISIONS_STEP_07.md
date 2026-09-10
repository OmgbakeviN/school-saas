# Décisions — STEP 07

## ADR-038 — Le compte de pension appartient à l'inscription annuelle

**Décision :** utiliser `Enrollment` comme parent du compte financier.

**Raison :** un élève permanent peut avoir plusieurs années scolaires et il ne
faut jamais mélanger les soldes.

## ADR-039 — La pension est composée de tranches

Le montant annuel est la somme des `TuitionInstallment` actives.

Cela correspond au fonctionnement réel des établissements qui encaissent la
pension par échéances.

## ADR-040 — Les paiements sont imputés automatiquement

Un paiement est appliqué aux tranches par ordre croissant.

Cela évite à l'utilisateur de devoir répartir manuellement chaque versement.

## ADR-041 — Pas de modification d'un paiement enregistré

Les paiements sont des événements financiers.

Une correction future devra passer par une opération inverse / avoir et non
par l'édition silencieuse de l'ancien paiement.

## ADR-042 — Un reçu est un snapshot

Le PDF créé au moment de l'encaissement est conservé tel quel.

## ADR-043 — Verrouiller la structure d'un plan après le premier paiement

Modifier les montants des tranches après des encaissements modifierait
rétroactivement la dette des élèves.

STEP 07 bloque donc cette opération.

## ADR-044 — Un comptable peut encaisser mais pas reconfigurer la pension

Le rôle `ACCOUNTANT` accède au suivi et aux reçus.

La définition des plans reste réservée à OWNER / DIRECTOR / MANAGER.
