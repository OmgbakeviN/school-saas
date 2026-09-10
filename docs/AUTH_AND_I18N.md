# JWT Refresh & Internationalisation

## Refresh token

Endpoint :

```text
POST /api/auth/refresh/
```

Politique actuelle :

- access token : 15 minutes ;
- refresh token : 7 jours ;
- pas de rotation du refresh token pour le moment.

Le client Axios intercepte automatiquement les réponses `401` éligibles :

```text
requête API
  ↓
401 (access expiré)
  ↓
POST /api/auth/refresh/
  ↓
nouvel access token
  ↓
rejeu automatique de la requête originale
```

Plusieurs requêtes expirées au même moment partagent la même promesse de refresh afin d'éviter plusieurs refresh simultanés.

Si le refresh token est lui-même expiré ou invalide :

- les tokens sont supprimés ;
- l'événement `be-wise-auth-expired` est envoyé ;
- le portail retourne à la connexion.

## Langues frontend

Source de vérité :

```text
frontend/src/i18n/fr.js
frontend/src/i18n/en.js
```

Provider :

```text
frontend/src/i18n/index.jsx
```

Utilisation :

```jsx
const { t } = useI18n();

<h1>{t("academics.title")}</h1>
```

Avec variable :

```jsx
t("academics.classroom.count", { count: 12 })
```

La préférence est conservée dans :

```text
localStorage["be-wise-language"]
```

Les nouveaux modules devront ajouter leurs textes dans `fr.js` et `en.js` au lieu d'écrire directement les libellés dans les composants.
