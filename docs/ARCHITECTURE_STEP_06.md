# Architecture — STEP 06

## Nouvelle application

```text
apps.report_cards
```

Elle dépend de :

```text
tenants
academics
people
teaching
assessments
```

mais `assessments` ne dépend pas de `report_cards`.

Cette direction de dépendance évite une boucle entre moteur de notes et
documents officiels.

## Live results vs official snapshot

Deux concepts sont volontairement séparés.

### Live result

Calculé à la demande depuis les évaluations publiées.

Utilisé pour :

- explorateur ;
- classements ;
- vues matière ;
- prévisualisation.

### Snapshot

Copie figée au moment de la publication.

Utilisé pour :

- PDF ;
- historique ;
- vérification ;
- futures demandes parent / WhatsApp.

Une modification ultérieure des notes ne change jamais un ancien snapshot.

## Intégrité

Deux empreintes sont stockées.

```text
payload_sha256
pdf_sha256
```

`payload_sha256` protège les données logiques figées.

`pdf_sha256` identifie les octets du document officiel généré.

## Versionnement

La version est séquentielle dans un même contexte :

```text
student + PERIOD + period
```

ou :

```text
student + ANNUAL + academic_year
```

La nouvelle version référence la précédente avec `supersedes`.

## Multi-tenancy

Tous les endpoints privés utilisent :

```text
request.school
```

et filtrent systématiquement par établissement.

La vérification publique ne dépend pas du tenant courant : le token long et
unique résout directement le snapshot.
