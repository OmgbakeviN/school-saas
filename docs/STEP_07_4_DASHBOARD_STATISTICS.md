# STEP 07.4 — Tableau de bord statistique

## Objectif

Transformer le tableau de bord établissement en une vue opérationnelle et
décisionnelle, sans ajouter de dépendance de graphiques et sans dupliquer les
règles métier existantes.

Les statistiques sont calculées à partir de l'année scolaire active. Si aucune
année n'est marquée active, la dernière année configurée est utilisée comme
fallback.

## Données affichées

### Indicateurs principaux

Pour la direction / gestion :

- élèves inscrits sur l'année active ;
- classes actives ;
- enseignants actifs ;
- taux de recouvrement si le rôle possède l'accès Finance ;
- sinon taux d'évaluations publiées.

Pour un enseignant :

- élèves appartenant à ses classes / affectations ;
- classes concernées ;
- affectations pédagogiques actives ;
- taux de publication de ses évaluations.

### Population

Le dashboard affiche :

- répartition par cycle ;
- répartition filles / garçons / autre / non renseigné ;
- effectifs des huit classes les plus chargées ;
- capacité de classe et taux d'occupation lorsqu'une capacité existe.

Les comptages sont basés sur `Enrollment` de l'année scolaire active et non sur
le simple nombre historique de `Student`.

### Activité pédagogique

Pour les rôles académiques :

- nombre d'évaluations ;
- workflow DRAFT / INPUT / SUBMITTED / VALIDATED / PUBLISHED ;
- taux de publication ;
- nombre de bulletins effectivement publiés ;
- moyenne annuelle lorsqu'elle est disponible.

Le nombre de bulletins est dédupliqué par élève / période afin qu'une version
v2 ou v3 du même bulletin ne gonfle pas la statistique.

### Finance

Visible uniquement aux rôles déjà autorisés au module Finance :

- pension attendue ;
- montant encaissé ;
- reste à encaisser ;
- taux de recouvrement ;
- comptes soldés / partiels / impayés ;
- montant encaissé aujourd'hui ;
- montant encaissé dans le mois ;
- évolution des encaissements sur les six derniers mois.

Les calculs de pension réutilisent le service Finance existant
`dashboard_summary`.

## Sécurité par rôle

Le endpoint reste :

```http
GET /api/tenant/dashboard/
```

mais ajoute une clé `analytics`.

La sécurité ne repose pas uniquement sur le frontend.

### OWNER / DIRECTOR / MANAGER

Statistiques établissement complètes selon leurs accès métiers.

### ACCOUNTANT

Statistiques générales et financières. Les statistiques pédagogiques ne sont
pas renvoyées.

### TEACHER

Les statistiques pédagogiques et de population sont limitées aux classes
auxquelles l'enseignant est lié par :

- `TeachingAssignment` ;
- ou `ClassroomLeadership`.

Aucune statistique financière n'est renvoyée.

## Format de réponse

Extrait :

```json
{
  "analytics": {
    "scope": "SCHOOL",
    "academic_year": {
      "id": 4,
      "name": "2026/2027",
      "progress": 18.4
    },
    "overview": {
      "students": 412,
      "classes": 15,
      "teachers": 28,
      "members": 6
    },
    "population": {
      "gender": [],
      "cycles": [],
      "classrooms": []
    },
    "academics": {},
    "finance": {},
    "generated_at": "..."
  }
}
```

## Frontend

Le dashboard est responsive sans bibliothèque de chart externe.

Les graphiques utilisent :

- barres CSS ;
- donut CSS ;
- progression ;
- colonnes mensuelles ;
- couleurs dynamiques de l'établissement.

Le thème reste donc cohérent avec `primary_color` et `secondary_color`.

Le dashboard recharge ses statistiques lorsque l'utilisateur revient sur
l'onglet `Tableau de bord`.

## Migration

Aucune migration.
