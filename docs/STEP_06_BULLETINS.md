# STEP 06 — Bulletins & publication des résultats

## Objectif

Transformer les résultats publiés de `apps.assessments` en documents officiels
consultables, exportables et vérifiables.

La chaîne devient :

```text
Assessment PUBLISHED
        ↓
moyennes / classements live
        ↓
prévisualisation du bulletin
        ↓
publication par la direction
        ↓
ReportCardSnapshot immuable
        ↓
PDF officiel + QR + empreintes SHA-256
```

## Explorateur

L'interface `Bulletins` permet plusieurs lectures.

### Par classe

```text
année
+ classe
+ période
```

Affiche :

- élèves ;
- moyenne générale ;
- rang ;
- matières ;
- accès au bulletin individuel.

### Par élève

Affiche le détail :

- toutes les matières ;
- moyenne par matière ;
- barème ;
- coefficient ;
- rang matière ;
- moyenne de classe ;
- moyenne générale ;
- rang général.

### Par matière

```text
classe
+ période
+ matière
```

Affiche :

- tous les élèves ;
- moyenne matière ;
- rang matière ;
- moyenne de la classe ;
- meilleure moyenne ;
- plus faible moyenne ;
- nombre d'évaluations publiées prises en compte.

### Annuel

Le mode annuel calcule :

```text
moyenne de chaque période × AcademicPeriod.weight
```

puis présente :

- moyenne annuelle ;
- rang annuel ;
- moyennes annuelles par matière ;
- décision de promotion déjà portée par `Enrollment`.

## Source de vérité

Aucune évaluation `DRAFT`, `INPUT`, `SUBMITTED` ou `VALIDATED` ne compte dans le
bulletin.

Seules les évaluations :

```text
Assessment.status = PUBLISHED
```

sont utilisées.

## Appréciations

Lors d'une publication individuelle, la direction peut renseigner :

- appréciation par matière ;
- appréciation du titulaire / responsable ;
- appréciation générale.

Si une appréciation matière ou titulaire reste vide, le backend génère une
appréciation simple à partir du ratio `moyenne / barème`.

La publication massive par classe utilise ces appréciations automatiques.

## Snapshot immuable

`ReportCardSnapshot` contient :

```text
school
enrollment
academic_year
academic_period nullable
report_type PERIOD | ANNUAL
version
supersedes
payload JSON figé
payload_sha256
verification_token
pdf_file
pdf_sha256
published_by
published_at
```

Une instance déjà sauvegardée ne peut pas être modifiée.

Une correction produit :

```text
bulletin v1
   ↓ supersedes
bulletin v2
   ↓
bulletin v3
```

L'historique reste consultable.

## PDF

Le PDF reprend automatiquement :

- nom de l'établissement ;
- devise ;
- coordonnées ;
- logo si disponible ;
- couleurs de branding ;
- élève / matricule ;
- classe / niveau ;
- titulaire ou professeur principal ;
- matières ;
- moyennes ;
- coefficients ;
- rangs ;
- moyenne de classe ;
- appréciations ;
- moyenne générale ;
- signatures textuelles ;
- QR de vérification ;
- version ;
- empreinte courte.

La génération utilise `ReportLab`.

## QR et vérification publique

Le QR pointe vers :

```text
/verify/report-card/<token>/
```

Le token est généré avec `secrets.token_urlsafe(32)`.

La page publique montre uniquement :

- authenticité ;
- établissement ;
- nom partiellement masqué de l'élève ;
- classe ;
- année ;
- période ;
- version ;
- date de publication ;
- empreinte.

Elle ne publie pas les notes.

L'API JSON de vérification existe aussi :

```text
GET /api/public/report-cards/verify/<token>/
```

## Permissions

### OWNER / DIRECTOR

- explorer tous les résultats ;
- publier un bulletin ;
- publier une classe entière ;
- télécharger les PDF ;
- consulter toutes les versions.

### MANAGER

- explorer les résultats ;
- consulter les bulletins publiés ;
- télécharger les PDF ;
- ne publie pas de document officiel.

### TEACHER

Un professeur peut voir un bulletin complet uniquement s'il est :

```text
CLASS_TEACHER
ou
HOMEROOM_TEACHER
```

de la classe.

Un enseignant par matière peut consulter le résultat de sa matière dans ses
classes, mais pas automatiquement le bulletin complet contenant les autres
matières.

## Présences

Le snapshot contient déjà :

```json
{
  "attendance": {
    "absences": null,
    "late_arrivals": null
  }
}
```

Cela permettra à STEP 07 d'injecter absences et retards sans casser le format
des bulletins historiques.

## Personnalisation future

STEP 06 fournit un modèle officiel propre, basé sur le branding de l'école.

Un éditeur avancé de modèles (colonnes, libellés, signatures graphiques,
orientation, entête ministériel, etc.) peut être ajouté plus tard sans modifier
le principe des snapshots immuables.


## Extension STEP 06.1

### Rangs ex æquo

Le classement utilise maintenant un rang dense :

```text
1, 1, 2, 3
```

### Publication intelligente

Une nouvelle version n'est créée que si le contenu significatif du bulletin a
changé.

### Export ZIP par classe

La dernière version publiée de chaque bulletin peut être téléchargée en une
archive ZIP avec un `manifest.txt`.

Voir `docs/STEP_06_1_AMELIORATIONS_BULLETINS.md`.
