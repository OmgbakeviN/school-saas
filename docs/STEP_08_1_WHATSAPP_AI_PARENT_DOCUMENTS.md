# STEP 08.1 — Agent WhatsApp IA : bulletins & facture de pension

## Objectif du MVP

Cette étape limite volontairement l'agent conversationnel à deux actions privées :

1. envoyer un bulletin de période déjà publié ;
2. générer et envoyer la facture / situation de pension PDF de l'élève.

Le parent parle naturellement à l'agent dans WhatsApp. n8n comprend la demande et appelle uniquement des outils Django autorisés.

```text
Parent WhatsApp
      ↓
Evolution API
      ↓ webhook
n8n AI Agent
      ↓ outils internes
BE WISE Django
      ↓
permissions + tenant + documents
      ↓
Evolution API
      ↓
PDF dans WhatsApp
```

## Principe de sécurité

n8n et le modèle IA ne lisent jamais PostgreSQL directement.

Django reste l'autorité pour :

- identifier l'établissement à partir de l'instance Evolution ;
- normaliser le numéro WhatsApp ;
- retrouver le parent vérifié ;
- vérifier le lien parent / élève ;
- vérifier les droits sur les résultats et la finance ;
- sélectionner le bulletin officiellement publié ;
- générer la facture de pension ;
- envoyer le document via le provider ;
- journaliser les messages et les documents envoyés.

L'agent ne reçoit que les enfants et documents déjà autorisés.

## Nouveaux modèles

### WhatsAppConnection

Une connexion WhatsApp par établissement pour ce MVP.

```text
School
  └── WhatsAppConnection
        provider = EVOLUTION
        instance_name
        phone_number
        is_active
```

`instance_name` est le nom exact de l'instance dans Evolution API.

### GuardianWhatsAppIdentity

Associe un parent à un numéro WhatsApp normalisé et vérifié.

```text
Guardian
  └── GuardianWhatsAppIdentity
        normalized_phone
        phone_verified
        whatsapp_enabled
        verified_at
```

Un numéro ne peut identifier qu'un seul parent dans le même établissement. Cela évite une résolution ambiguë de l'identité.

### StudentGuardianDocumentPermission

Permission supplémentaire propre aux documents WhatsApp :

```text
StudentGuardian
  └── can_receive_report_cards
      can_receive_finance
```

Pour un bulletin, `StudentGuardian.can_receive_results` doit également être vrai.

### WhatsAppMessageLog

Journal technique multi-tenant des messages entrants / sortants et documents envoyés.

## Identification d'un parent

Le numéro entrant est normalisé au format international :

```text
690000001
→ +237690000001

237690000001@s.whatsapp.net
→ +237690000001
```

Pour qu'un parent soit autorisé :

```text
GuardianWhatsAppIdentity.phone_verified = true
GuardianWhatsAppIdentity.whatsapp_enabled = true
Guardian.is_active = true
```

Un numéro inconnu ou non vérifié ne reçoit aucune donnée privée.

## Contexte fourni à l'agent

Endpoint :

```http
POST /api/whatsapp-ai/context/
X-Bewise-Agent-Key: <secret>
```

Payload :

```json
{
  "instance_name": "pionniers-local",
  "phone": "237690000001",
  "message_text": "Envoie-moi le bulletin du premier trimestre de Kevin"
}
```

Django retourne uniquement le périmètre autorisé, par exemple :

```json
{
  "authorized": true,
  "school": {
    "name": "École Primaire Les Pionniers de Yaoundé",
    "slug": "pionniers-yaounde"
  },
  "guardian": {
    "name": "Omgba Mireille",
    "preferred_language": "FR"
  },
  "children": [
    {
      "student_id": 12,
      "name": "Omgba Kevin",
      "classroom": "CM2 A",
      "permissions": {
        "report_cards": true,
        "finance": true
      },
      "available_report_cards": [
        {
          "period_name": "1er trimestre",
          "period_order": 1,
          "version": 2,
          "language": "FR"
        }
      ],
      "tuition_invoice_available": true
    }
  ],
  "capabilities": [
    "SEND_PERIOD_REPORT_CARD",
    "SEND_TUITION_INVOICE"
  ]
}
```

Les IDs sont nécessaires aux appels outil mais l'agent reçoit l'instruction de ne jamais les afficher au parent.

## Outil 1 — bulletin de trimestre / période

Endpoint :

```http
POST /api/whatsapp-ai/tools/send-term-report-card/
```

Payload :

```json
{
  "instance_name": "pionniers-local",
  "phone": "237690000001",
  "student_id": 12,
  "period": "1er trimestre"
}
```

Le backend :

```text
numéro vérifié
→ parent
→ lien parent/élève
→ can_receive_results
→ can_receive_report_cards
→ inscription courante
→ dernier ReportCardSnapshot publié de la période
→ lit le PDF officiel existant
→ Evolution API sendMedia(document)
```

Le bulletin n'est pas régénéré. Le PDF envoyé est exactement le snapshot officiel déjà publié par la direction.

Le sélecteur de période comprend notamment :

```text
1
1er
premier
first
2 / deuxième / second
3 / troisième / third
latest / dernier
```

Le même mécanisme fonctionne avec des semestres ou périodes personnalisées lorsque le nom de période est fourni.

## Outil 2 — facture de pension PDF

Endpoint :

```http
POST /api/whatsapp-ai/tools/send-tuition-invoice/
```

Payload :

```json
{
  "instance_name": "pionniers-local",
  "phone": "237690000001",
  "student_id": 12
}
```

Le backend vérifie `can_receive_finance`, retrouve le `StudentTuitionAccount`, calcule la situation via le service Finance existant et génère un PDF A4.

Le document contient :

- établissement et branding ;
- élève, matricule, classe, année scolaire ;
- plan de pension ;
- toutes les tranches ;
- montant par tranche ;
- montant payé ;
- reste par tranche ;
- échéance ;
- pension annuelle ;
- total payé ;
- reste global.

La facture est FR ou EN selon `Guardian.preferred_language`.

Cette facture est un état actuel de la pension. Elle ne remplace pas les reçus immuables déjà générés après chaque paiement.

## Prévisualiser localement la facture

Endpoint volontairement réservé à la clé interne :

```http
POST /api/whatsapp-ai/tools/preview-tuition-invoice/
```

Il renvoie le PDF inline sans contacter Evolution API.

## Réponse texte de l'agent

Après son raisonnement et/ou un appel outil, n8n envoie la réponse finale avec :

```http
POST /api/whatsapp-ai/send-text/
```

Cela permet de garder également l'envoi texte derrière la même abstraction provider et le même journal Django.

## Provider Evolution API

Le provider Django expose actuellement :

```python
send_text(...)
send_document(...)
```

L'implémentation Evolution convertit le PDF en base64 et l'envoie comme document PDF. Le reste du code ne dépend pas des détails du provider.

Une implémentation Meta Cloud pourra donc être ajoutée plus tard sans modifier les règles d'autorisation.

## Mode local DRY RUN

En local :

```env
WHATSAPP_AI_DRY_RUN=True
```

Les endpoints exécutent toutes les vérifications, lisent ou génèrent le document et enregistrent le log, mais aucun appel réseau n'est envoyé à Evolution.

C'est le mode recommandé pour le premier test.

## Migration

```text
whatsapp_ai.0001_initial
```

Aucune modification frontend dans cette étape.
