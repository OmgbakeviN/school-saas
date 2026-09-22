# BE WISE School — STEP 08.1
## Agent WhatsApp IA : bulletin de période + facture de pension PDF

Cette livraison ajoute le premier MVP conversationnel WhatsApp sans modifier le frontend.

## Ce qui est livré

```text
Django WhatsApp AI app
Evolution provider abstraction
identité parent WhatsApp vérifiée
permissions documents par parent/élève
bulletin de période publié
facture de pension PDF FR/EN
logs messages/documents
API interne protégée
mode DRY RUN local
workflow n8n importable
prompt agent sécurisé
management command de setup
tests backend
```

## Migration

```text
whatsapp_ai.0001_initial
```

## 1. Installation locale

Extraire ce ZIP à la racine du projet.

Puis :

```powershell
cd "C:\Users\dell\school saas"
.venv\Scripts\Activate.ps1

cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py check
```

## 2. Variables locales

Dans votre `.env` local :

```env
WHATSAPP_AGENT_API_KEY=local-super-secret-change-me
WHATSAPP_DEFAULT_COUNTRY_CODE=237
WHATSAPP_AI_DRY_RUN=True

# Non obligatoires tant que DRY RUN=True
EVOLUTION_API_URL=
EVOLUTION_API_KEY=
EVOLUTION_API_TIMEOUT=30
```

Redémarrer Django après modification du `.env`.

## 3. Préparer une école de test

Exemple :

```powershell
python manage.py setup_whatsapp_mvp `
  --school pionniers-yaounde `
  --instance pionniers-local `
  --verify-guardians `
  --enable-finance
```

`--verify-guardians` sert uniquement au test local ou après une vraie vérification du numéro.

Il initialise :

- l'instance WhatsApp de l'école ;
- les numéros parents normalisés ;
- les permissions bulletin ;
- les permissions finance avec `--enable-finance`.

## 4. Test contexte sans n8n

Avec Django lancé :

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/whatsapp-ai/context/" `
  -H "Content-Type: application/json" `
  -H "X-Bewise-Agent-Key: local-super-secret-change-me" `
  -d '{"instance_name":"pionniers-local","phone":"237690000001","message_text":"Je veux le bulletin du premier trimestre"}'
```

Le JSON doit retourner :

```text
authorized: true
children: [...]
available_report_cards: [...]
tuition_invoice_available: true/false
```

## 5. Test facture PDF sans Evolution

Récupérer le `student_id` autorisé retourné par le contexte, puis :

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/whatsapp-ai/tools/preview-tuition-invoice/" `
  -H "Content-Type: application/json" `
  -H "X-Bewise-Agent-Key: local-super-secret-change-me" `
  -d '{"instance_name":"pionniers-local","phone":"237690000001","student_id":1}' `
  --output facture-test.pdf
```

Ouvrir `facture-test.pdf`.

## 6. Test des deux outils en DRY RUN

Bulletin :

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/whatsapp-ai/tools/send-term-report-card/" `
  -H "Content-Type: application/json" `
  -H "X-Bewise-Agent-Key: local-super-secret-change-me" `
  -d '{"instance_name":"pionniers-local","phone":"237690000001","student_id":1,"period":"1er trimestre"}'
```

Facture :

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/whatsapp-ai/tools/send-tuition-invoice/" `
  -H "Content-Type: application/json" `
  -H "X-Bewise-Agent-Key: local-super-secret-change-me" `
  -d '{"instance_name":"pionniers-local","phone":"237690000001","student_id":1}'
```

En mode DRY RUN, la réponse doit contenir :

```json
{
  "sent": true,
  "dry_run": true
}
```

Aucun message WhatsApp réel n'est envoyé.

## 7. Tests Django

```powershell
python manage.py test apps.whatsapp_ai
```

## 8. n8n

Importer :

```text
n8n/BE_WISE_WhatsApp_Parent_Documents_AI.json
```

Puis suivre :

```text
docs/N8N_SETUP_STEP_08_1.md
```

## Validation effectuée lors de la génération

- syntaxe Python vérifiée ;
- JSON n8n parsé ;
- structure des routes/config vérifiée ;
- génération réelle de la facture FR effectuée ;
- génération réelle de la facture EN effectuée ;
- les deux factures tiennent sur une page A4 ;
- rendus PDF inspectés visuellement ;
- ZIP vérifié.

Les tests Django runtime doivent encore être exécutés dans votre `.venv` locale, car Django n'est pas disponible dans l'environnement de génération.
