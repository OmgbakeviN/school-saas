# STEP 03.2.3 — Backend route correction

This ZIP is intentionally BACKEND-ONLY.

Extract its contents directly inside:

```text
C:\Users\dell\school saas\backend
```

The ZIP starts with:

```text
apps/
config/
requirements.txt
```

Do NOT extract it one folder above unless you deliberately merge those paths.

The canonical export URLs are:

```text
/api/people/exports/students/
/api/people/exports/teachers/
/api/people/exports/guardians/
/api/people/exports/enrollments/
```

Legacy aliases are also kept:

```text
/api/people/bulk/export/students/
/api/people/bulk/export/teachers/
/api/people/bulk/export/guardians/
/api/people/bulk/export/enrollments/
```

No migration is required.
