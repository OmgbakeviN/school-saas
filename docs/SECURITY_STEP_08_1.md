# Sécurité — STEP 08.1 WhatsApp IA

## Règle principale

L'agent IA ne possède jamais de permission métier propre.

Il peut demander une action ; Django décide si cette action est autorisée.

## Clé n8n → Django

Les endpoints `/api/whatsapp-ai/` utilisent :

```http
X-Bewise-Agent-Key: <secret>
```

Cette clé est comparée avec `WHATSAPP_AGENT_API_KEY` côté serveur.

La clé doit être :

- longue et aléatoire ;
- différente des JWT utilisateurs ;
- stockée dans les variables d'environnement ;
- jamais commitée dans Git ;
- jamais exposée dans le frontend navigateur.

## Double contrôle identité + permission

Un appel outil ne fait jamais confiance au `student_id` donné par l'IA.

Pour chaque document, Django refait :

```text
instance Evolution active
→ school
→ téléphone normalisé
→ GuardianWhatsAppIdentity vérifiée
→ StudentGuardian appartient au même school
→ student_id appartient réellement à ce parent
→ permissions du lien
→ document disponible
```

## Bulletin

Conditions :

```text
GuardianWhatsAppIdentity.phone_verified
GuardianWhatsAppIdentity.whatsapp_enabled
StudentGuardian.can_receive_results
StudentGuardianDocumentPermission.can_receive_report_cards
ReportCardSnapshot PERIOD existant
```

Seul le PDF publié déjà stocké est envoyé.

## Finance

Conditions :

```text
GuardianWhatsAppIdentity.phone_verified
GuardianWhatsAppIdentity.whatsapp_enabled
StudentGuardianDocumentPermission.can_receive_finance
StudentTuitionAccount existant
```

L'agent n'a aucun endpoint pour créer un paiement, modifier une tranche ou changer un plan de pension.

## Numéro inconnu

Le contexte retourne seulement :

```text
authorized = false
reason = UNKNOWN_OR_UNVERIFIED_PHONE
message générique
```

Aucun nom d'élève, aucune classe, aucun montant et aucun résultat n'est retourné.

## Conversation memory

La mémoire n8n est utile pour le langage naturel mais n'est jamais une source d'autorisation.

Le backend recharge les permissions à chaque message et à chaque appel outil.

## Logs

`WhatsAppMessageLog` permet d'auditer :

- texte entrant ;
- texte sortant ;
- document envoyé ;
- parent résolu ;
- numéro ;
- outil utilisé ;
- IDs internes utiles à l'audit ;
- ID message provider lorsque disponible.

Ces logs sont accessibles côté administration serveur, pas au parent.
