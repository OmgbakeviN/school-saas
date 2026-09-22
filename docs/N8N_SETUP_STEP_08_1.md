# n8n — Setup STEP 08.1

## Fichier à importer

```text
n8n/BE_WISE_WhatsApp_Parent_Documents_AI.json
```

Le workflow contient :

```text
Evolution Incoming Webhook
→ Normalize Evolution Message
→ Load Authorized Parent Context
→ Prepare Agent Input
→ BE WISE Parent Documents Agent
   ├── OpenAI Chat Model
   ├── Conversation Memory
   ├── send_term_report_card
   └── send_tuition_invoice
→ Send Agent Reply
```

## 1. Variables n8n

Configurer dans l'environnement du conteneur / service n8n :

```env
BEWISE_API_BASE=https://school.bewiseinnovation.com
BEWISE_AGENT_KEY=<même secret que WHATSAPP_AGENT_API_KEY côté Django>
```

Ne mettez jamais ces secrets directement dans le JSON du workflow.

## 2. Credential OpenAI

Après import :

1. ouvrir `OpenAI Chat Model` ;
2. sélectionner ou créer le credential OpenAI ;
3. sauvegarder le workflow.

Le modèle contenu dans le JSON est un choix de départ ; il peut être remplacé depuis n8n sans modifier le backend.

## 3. Webhook Evolution

Activer le workflow puis copier son URL de webhook de production.

Configurer l'instance Evolution de l'établissement pour envoyer les événements de nouveaux messages à :

```text
https://<votre-n8n>/webhook/bewise-whatsapp-parent-documents
```

Le workflow ignore :

- les messages envoyés par le bot lui-même (`fromMe`) ;
- les groupes ;
- les événements sans texte exploitable.

## 4. Routage multi-école

Evolution fournit le nom d'instance dans le webhook.

n8n transmet :

```text
instance_name
phone
message_text
```

Django résout ensuite :

```text
instance_name
→ WhatsAppConnection
→ School
```

Il ne faut donc pas coder un `school_id` dans n8n.

## 5. Mémoire conversationnelle

La session n8n est indexée par :

```text
<instance_name>:<phone>
```

Deux établissements utilisant le même numéro parent restent donc séparés.

La mémoire sert seulement à comprendre les références conversationnelles comme :

```text
Parent : Envoie le bulletin de Kevin du premier trimestre.
Agent  : [envoi]
Parent : Et sa facture de pension ?
```

À chaque message, les autorisations réelles sont rechargées depuis Django. La mémoire ne remplace jamais les permissions du backend.

## 6. Outils de l'agent

### send_term_report_card

Le modèle fournit :

```text
student_id
period
```

Ces valeurs doivent provenir du `AUTHORIZED CONTEXT JSON`.

### send_tuition_invoice

Le modèle fournit :

```text
student_id
```

Django revalide toujours le parent, l'enfant et les permissions avant l'envoi.

## 7. Si HTTP Request Tool n'est pas disponible

Selon la version / installation de n8n, le nom ou la disponibilité du nœud outil HTTP peut varier.

Si le workflow signale que `httpRequestTool` est inconnu :

1. créer un nœud `HTTP Request` utilisable comme Tool dans l'AI Agent ;
2. conserver exactement les mêmes URLs ;
3. conserver le header `X-Bewise-Agent-Key` ;
4. conserver les mêmes payloads JSON ;
5. connecter le nœud à l'entrée `Tool` de l'agent.

Aucune modification Django n'est nécessaire.

## 8. Premier scénario de test

Parent :

```text
Bonjour, envoie-moi le bulletin du premier trimestre de Kevin.
```

Attendu :

```text
contexte autorisé
→ sélection Kevin
→ outil bulletin
→ PDF WhatsApp
→ confirmation courte
```

Puis :

```text
Envoie-moi aussi sa facture de pension.
```

Attendu :

```text
mémoire = Kevin
→ outil facture
→ PDF WhatsApp
→ confirmation courte
```
