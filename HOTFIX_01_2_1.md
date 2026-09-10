# HOTFIX 01.2.1 — Tests multi-tenant

## Correction

- [x] Les tests d'isolation n'utilisent plus `X-Tenant-Slug` comme mécanisme principal.
- [x] Les tests utilisent maintenant de vrais hostnames :
  - `ecole-a.localhost`
  - `ecole-b.localhost`
- [x] Ajout d'une assertion explicite sur la réponse de login.
- [x] Ajout d'un troisième test vérifiant que `X-Tenant-Slug` fonctionne bien lorsque `DEBUG=True`.

## Pourquoi le test précédent échouait

Django force normalement `DEBUG=False` pendant l'exécution des tests.

Or le middleware BE WISE accepte volontairement :

```http
X-Tenant-Slug
```

uniquement lorsque `DEBUG=True`.

Le test précédent dépendait donc d'un mécanisme de développement qui était désactivé par le test runner.

Ce comportement est souhaité pour la sécurité en production.

## Commande

```bash
cd backend
python manage.py test apps.tenants
```

Résultat attendu :

```text
Found 3 test(s).
...
OK
```

Aucune migration n'est nécessaire.
