# STEP 03.2 — Imports, affectations massives & fin d'année

Cette étape ajoute les opérations administratives de masse au module `people`.

## 1. Imports CSV / XLSX

Endpoints :

```text
POST /api/people/bulk/import/students/
POST /api/people/bulk/import/teachers/
POST /api/people/bulk/import/guardians/
```

Les imports acceptent :

```text
.csv
.xlsx
```

Le mode `dry_run=true` valide le fichier sans enregistrer.

Pour les élèves, l'import peut recevoir `classroom` afin de créer aussi
l'inscription annuelle.

Modèles CSV :

```text
GET /api/people/bulk/import-template/students/
GET /api/people/bulk/import-template/teachers/
GET /api/people/bulk/import-template/guardians/
```

## 2. Affectation massive

```text
POST /api/people/bulk/class-assignment/
```

Le frontend permet de cocher plusieurs élèves.

Si un élève possède déjà une inscription pour l'année sélectionnée,
l'inscription est déplacée vers la classe cible au lieu d'être dupliquée.

## 3. Fin d'année

Prévisualisation :

```text
POST /api/people/promotion/preview/
```

Le moteur cherche le seuil dans cet ordre :

```text
niveau
  ↓
cycle
  ↓
établissement
```

Puis :

```text
moyenne >= seuil → PROMOTED suggéré
moyenne < seuil  → REPEATED suggéré
pas de moyenne   → PENDING
```

La suggestion n'est jamais une décision définitive.

Application :

```text
POST /api/people/promotion/apply/
```

Décisions :

```text
PROMOTED
REPEATED
GRADUATED
TRANSFERRED
WITHDRAWN
```

`PROMOTED` et `REPEATED` nécessitent une classe de destination appartenant
à une autre année scolaire.

## 4. Réinscription des redoublants

Endpoint spécialisé :

```text
POST /api/people/promotion/re-enroll-repeaters/
```

Il crée l'inscription de l'année suivante et relie :

```text
ancienne Enrollment
      ↓ next_enrollment
nouvelle Enrollment
```

## 5. Transfert / sortie

```text
POST /api/people/promotion/exit/
```

Actions :

```text
TRANSFERRED
WITHDRAWN
```

La fiche `Student` et l'inscription annuelle sont mises à jour ensemble.

## 6. Assistant nouvelle année

```text
POST /api/people/academic-years/prepare/
```

L'assistant peut recopier :

```text
classes
périodes
```

Les matières par niveau ne sont pas copiées car `LevelSubject` est déjà
persistant indépendamment de l'année scolaire.

## 7. Exports

```text
GET /api/people/bulk/export/students/?format=csv
GET /api/people/bulk/export/students/?format=xlsx
GET /api/people/bulk/export/teachers/?format=xlsx
GET /api/people/bulk/export/guardians/?format=xlsx
GET /api/people/bulk/export/enrollments/?format=xlsx
```

Les élèves et inscriptions peuvent être filtrés par :

```text
academic_year
classroom
```

## Swagger

Les nouveaux endpoints utilisent `extend_schema`.

Le patch corrige également les warnings Spectacular existants sur :

```text
bootstrap_structure
bulk_assign_subject
bootstrap_periods
academic_policy
health
people_summary
public_context
create_school
tenant_dashboard
school_members
school_member_detail
school_settings
```

et documente les `SerializerMethodField` signalés.

Validation :

```powershell
python manage.py spectacular --validate --file openapi-schema.yml
```

## Migration

Aucune nouvelle migration.
