# Cause réelle du 404 des exports

Le routing Django était correct.

La preuve était :

```text
resolve('/api/people/exports/students/')
-> StudentExportView
```

mais :

```text
GET /api/people/exports/teachers/?format=xlsx
-> 404 {"detail":"Non trouvé."}
```

La cause est le paramètre `format`.

Django REST Framework réserve par défaut :

```text
?format=
```

pour la négociation du renderer HTTP.

Ainsi :

```text
?format=xlsx
```

est intercepté AVANT l'exécution de `StudentExportView` /
`TeacherExportView`.

Comme aucun renderer DRF nommé `xlsx` n'existe, DRF lève un `Http404`.
C'est pourquoi l'URL se résout correctement mais la requête retourne 404.

## Correction

1. `REST_FRAMEWORK["URL_FORMAT_OVERRIDE"] = None`
2. le paramètre canonique d'export devient `file_format`
3. le frontend envoie `?file_format=xlsx`
4. le backend accepte encore `?format=xlsx` pour compatibilité

Exemples :

```text
/api/people/exports/students/?file_format=xlsx&academic_year=2
/api/people/exports/teachers/?file_format=csv
```

Aucune migration.
