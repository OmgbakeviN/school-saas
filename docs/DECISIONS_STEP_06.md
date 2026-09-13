# Décisions — STEP 06

## ADR-031 — Les bulletins publiés sont des snapshots immuables

**Décision :** ne jamais recalculer dynamiquement un bulletin officiel déjà
publié.

**Raison :** un document remis à un parent doit rester identique même si une
note est corrigée plus tard.

## ADR-032 — Une correction crée une version

**Décision :**

```text
v1 → v2 → v3
```

plutôt que de remplacer le fichier.

**Raison :** auditabilité et traçabilité.

## ADR-033 — Seules les évaluations PUBLISHED alimentent les bulletins

Les brouillons, saisies en cours, soumissions et validations intermédiaires ne
sont jamais considérés comme résultats officiels.

## ADR-034 — Le QR n'expose pas les notes publiquement

La page publique confirme l'authenticité du document mais ne retourne pas le
détail académique.

## ADR-035 — Le professeur principal n'accède pas implicitement à toutes les notes

Le bulletin complet est visible à un professeur lorsqu'il exerce une
responsabilité de classe (`CLASS_TEACHER` ou `HOMEROOM_TEACHER`).

Un enseignant de matière reste limité à ses matières pour l'explorateur.

## ADR-036 — PDF généré au moment de la publication

Le PDF est enregistré dans `MEDIA_ROOT` lors de la création du snapshot.

Il n'est pas reconstruit lors de chaque téléchargement.

## ADR-037 — `file_format` reste la convention pour les autres exports

STEP 06 n'utilise pas `?format=` pour ses PDF et conserve la correction déjà
effectuée sur Django REST Framework.


## Extension STEP 06.2

Les décisions ADR-045 à ADR-049 concernant les modèles contrôlés, la portée par
cycle, le gel du template dans le snapshot, la règle une-page A4 et la
prévisualisation non officielle sont détaillées dans :

```text
docs/DECISIONS_STEP_06_2.md
```
