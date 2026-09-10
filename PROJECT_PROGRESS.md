# BE WISE School — Progression du projet

## Fondation

- [x] Multi-tenant School / SchoolMembership / User
- [x] Sous-domaines tenant
- [x] JWT access + refresh
- [x] Branding établissement
- [x] Membres et rôles
- [x] Swagger / OpenAPI avec drf-spectacular
- [x] FR / EN

## Étape 2 — Structure académique

- [x] AcademicYear
- [x] Section
- [x] Cycle
- [x] Level
- [x] Classroom annuelle
- [x] AcademicPeriod
- [x] Subject
- [x] LevelSubject
- [x] coefficients
- [x] règles de notation
- [x] seuils de promotion niveau → cycle → établissement

## Étape 3.1 — Personnes & inscriptions

- [x] Student permanent
- [x] Teacher permanent
- [x] Guardian
- [x] liens parent ↔ enfant
- [x] Enrollment annuel
- [x] historique scolaire

## Étape 3.2 — Opérations administratives

- [x] Import élèves CSV / Excel
- [x] Import enseignants CSV / Excel
- [x] Import parents / tuteurs
- [x] Affectation massive d'élèves à une classe
- [x] Promotion de fin d'année
- [x] Réinscription des redoublants
- [x] Transfert / sortie
- [x] Assistant de préparation de la nouvelle année
- [x] Export CSV / XLSX
- [x] correction conflit DRF `format` → `file_format`

## Étape 4 — Affectations pédagogiques

- [x] Teacher + Subject + Classroom + AcademicYear
- [x] Titulaire de classe
- [x] Professeur principal
- [x] Permission `can_enter_scores`
- [x] espace professeur et login TEACHER
- [x] création / liaison / révocation d'un compte enseignant
- [x] changement de mot de passe
- [x] Swagger Teaching
- [x] adaptation primaire : titulaire → toutes les matières du programme de la classe
- [x] adaptation hybride : titulaire automatique + affectations manuelles spécialistes
- [x] professeur principal sans droit implicite de saisie
- [x] affectations automatiques traçables `CLASS_TEACHER_AUTO`

## Étape 5 — Évaluations & notes

- [x] application Django `assessments`
- [x] Assessment lié à TeachingAssignment + AcademicPeriod
- [x] types interrogation / devoir / examen / oral / pratique / autre
- [x] barème propre à chaque évaluation
- [x] poids propre à chaque évaluation
- [x] contrôle admin de l'ouverture des périodes de saisie
- [x] saisie des notes uniquement sur une affectation autorisée
- [x] carnet de notes par classe avec ABS / dispensé / commentaire
- [x] workflow DRAFT → INPUT → SUBMITTED → VALIDATED → PUBLISHED
- [x] soumission bloquée si des élèves n'ont aucun état de note
- [x] validation et publication réservées OWNER / DIRECTOR
- [x] verrouillage des notes après soumission / publication
- [x] réouverture explicite par la direction
- [x] calcul des moyennes matière à partir des évaluations publiées
- [x] normalisation des barèmes des évaluations vers le barème de la matière
- [x] coefficient LevelSubject appliqué à la moyenne générale de période
- [x] poids AcademicPeriod appliqué à la moyenne annuelle
- [x] recalcul de `Enrollment.final_average`
- [x] résultats classe / période
- [x] interface direction et interface enseignant
- [x] FR / EN
- [x] Swagger Assessments
- [x] tests de workflow ajoutés
- [x] documentation mise à jour
- [x] évaluations disponibles sur toutes les matières du titulaire en mode Titulaire/Hybride

## Règle de sécurité de STEP 05 / 05.1

Le backend détermine d'abord le modèle pédagogique de l'établissement.

### Enseignant par matière

```text
compte TEACHER actif
        +
Teacher.user correspondant
        +
TeachingAssignment MANUAL active
        +
même AcademicYear
        +
même Classroom
        +
même Subject
        +
can_enter_scores = True
```

### Titulaire de classe / Hybride

```text
compte TEACHER actif
        +
Teacher.user correspondant
        +
ClassroomLeadership = CLASS_TEACHER actif
        +
même AcademicYear
        +
même Classroom
        +
Subject présent dans LevelSubject actif du niveau
        ↓
TeachingAssignment CLASS_TEACHER_AUTO
```

Puis, dans tous les cas :

```text
Assessment.status = INPUT
        +
période ouverte OU réouverture explicite par la direction
```

`HOMEROOM_TEACHER` / professeur principal ne donne jamais, à lui seul,
un droit de saisie.

Le frontend ne constitue jamais la source de vérité pour cette permission.

## Étape 6 — Bulletins & publication

- [x] application Django `report_cards`
- [x] explorateur par classe
- [x] vue bulletin d'un élève
- [x] vue résultat d'une matière
- [x] bulletin de période
- [x] bulletin annuel
- [x] classement général
- [x] classement par matière
- [x] moyenne de classe / min / max matière
- [x] appréciations par matière
- [x] appréciation titulaire / responsable
- [x] appréciation direction
- [x] appréciations automatiques pour publication massive
- [x] publication individuelle
- [x] publication massive par classe
- [x] snapshot immuable `ReportCardSnapshot`
- [x] historique des versions
- [x] relation `supersedes`
- [x] génération PDF officielle
- [x] branding école dans le PDF
- [x] QR code avec token long et imprévisible
- [x] empreinte SHA-256 du payload
- [x] empreinte SHA-256 du PDF
- [x] page publique de vérification
- [x] API publique de vérification
- [x] confidentialité : aucune note sur la page publique
- [x] permissions spécifiques TEACHER / MANAGER / DIRECTION
- [x] Swagger Report Cards
- [x] FR / EN
- [x] tests backend ajoutés
- [x] documentation mise à jour
- [ ] éditeur avancé de modèles de bulletin — option future

## Règle de publication STEP 06

```text
Assessment PUBLISHED
        ↓
résultats live
        ↓
publication OWNER / DIRECTOR
        ↓
ReportCardSnapshot
        ↓
PDF officiel immuable
```

Une correction ne modifie jamais un ancien bulletin :

```text
v1 → v2 → v3
```

## Étape 7 — Pension & paiements

- [x] application Django `finance`
- [x] plans de pension par année
- [x] plan applicable à un niveau
- [x] plan applicable à une classe
- [x] plan applicable à toute l'année
- [x] tranches de pension
- [x] échéances optionnelles
- [x] compte pension lié à `Enrollment`
- [x] affectation massive des plans aux élèves
- [x] gestion des conflits avec comptes déjà payés
- [x] statut `UNPAID / PARTIAL / PAID`
- [x] détail du solde par tranche
- [x] enregistrement des paiements
- [x] espèces
- [x] Mobile Money
- [x] virement bancaire
- [x] carte / autre
- [x] référence de transaction
- [x] imputation automatique sur les tranches
- [x] blocage du trop-perçu
- [x] numéro unique de reçu
- [x] génération PDF du reçu
- [x] branding de l'école sur le reçu
- [x] snapshot immuable du reçu
- [x] empreinte SHA-256 payload / PDF
- [x] historique des paiements
- [x] tableau de bord financier
- [x] pension attendue / encaissée / restante
- [x] taux de recouvrement
- [x] encaissements du jour
- [x] filtres année / classe / statut / recherche
- [x] permissions ACCOUNTANT
- [x] verrouillage du plan après premier paiement
- [x] Swagger Finance
- [x] FR / EN
- [x] tests backend
- [x] documentation mise à jour

## Prochaine étape recommandée — Étape 8

- [ ] emploi du temps
- [ ] salles
- [ ] présences élèves
- [ ] absences
- [ ] retards
- [ ] présence enseignants

## Point de reprise

Le format du snapshot STEP 06 contient déjà des champs `attendance` afin que
STEP 08 puisse injecter absences et retards dans les futurs bulletins sans
modifier les anciens documents.


---

## STEP 06.1 — Améliorations bulletins

- [x] classement dense `1, 1, 2, 3`
- [x] ex æquo général
- [x] ex æquo par matière
- [x] libellé explicite pour décision PENDING
- [x] publication uniquement si le contenu a changé
- [x] tentative identique = version actuelle conservée
- [x] modification réelle = nouvelle version
- [x] publication massive avec compteur `unchanged`
- [x] téléchargement ZIP des bulletins d'une classe
- [x] ZIP basé sur la dernière version publiée de chaque élève
- [x] `manifest.txt` dans le ZIP
- [x] liste des élèves sans bulletin dans le manifest
- [x] interface bouton ZIP
- [x] Swagger mis à jour
- [x] tests backend ajoutés
- [x] documentation mise à jour

Aucune migration.


---

## HOTFIX 07.1 — Formulaire de paiement responsive

- [x] fenêtre de paiement limitée à la hauteur réelle du viewport (`100dvh`)
- [x] contenu central scrollable sans dépasser l'écran
- [x] en-tête toujours visible
- [x] boutons Annuler / Enregistrer toujours accessibles
- [x] liste des tranches limitée en hauteur et scrollable
- [x] comportement amélioré sur petits écrans et fenêtres de faible hauteur
- [x] aucun hard refresh ajouté

Aucune migration.
