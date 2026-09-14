# STEP 06.2.2 - Bulletins FR/EN automatiques

## Objectif

Le bulletin officiel est maintenant rendu dans la langue académique de l'élève,
indépendamment de la langue de l'interface utilisée par l'administrateur.

## Résolution de la langue

Chaque `ReportCardTemplate` possède `language_mode` :

- `AUTO` : suit la section académique de l'élève ;
- `FRENCH` : force le bulletin en français ;
- `ENGLISH` : force le bulletin en anglais.

En mode `AUTO` :

```text
Section FRENCH  -> FR
Section ENGLISH -> EN
Section BILINGUAL
  -> langue de l'établissement si FRENCH ou ENGLISH
  -> sinon FR comme fallback déterministe
```

Le cas normal d'une école bilingue reste donc :

```text
Section Francophone -> bulletin FR
Section Anglophone   -> report card EN
```

## Données figées dans le snapshot

Chaque nouveau bulletin publié contient :

```json
{
  "language": {
    "code": "EN",
    "label": "English",
    "mode": "AUTO",
    "source": "SECTION",
    "section_language": "ENGLISH"
  },
  "template": {
    "language_mode": "AUTO"
  }
}
```

La langue fait partie du contenu significatif. Changer la langue du modèle ou
la section crée donc une nouvelle version du bulletin lors de la prochaine
publication. Les anciens snapshots restent immuables.

## Éléments PDF localisés

Le moteur localise notamment :

- titre du bulletin ;
- mention aperçu non officiel ;
- année scolaire / academic year ;
- élève / student ;
- matricule / student ID ;
- classe, niveau, effectif ;
- en-têtes du tableau des matières ;
- rang, moyenne de classe, moyenne générale ;
- décision annuelle ;
- appréciations automatiques ;
- appréciation du titulaire ;
- direction / school administration ;
- bloc de vérification QR ;
- termes et semestres standards.

Les données saisies librement par l'école ou les enseignants ne sont pas
traduites automatiquement : nom des matières, nom des classes, devise,
appréciations manuelles, etc. Cela évite de modifier un contenu pédagogique
rédigé intentionnellement.

## Exemples

```text
AUTO + Section Francophone
-> BULLETIN DE NOTES
-> Année scolaire
-> Élève
-> Matière
-> Moyenne générale
```

```text
AUTO + English Section
-> REPORT CARD
-> Academic Year
-> Student
-> Subject
-> Overall Average
```

## Migration

```text
report_cards.0003_reportcardtemplate_language_mode
```

## Compatibilité avec les bulletins déjà publiés

Avant STEP 06.2.2, les PDF étaient implicitement français. La comparaison de
contenu traite donc un ancien snapshot sans champ `language` comme `FR` et un
ancien template sans `language_mode` comme `AUTO`.

Conséquence :

```text
ancien bulletin français + aucun changement visible
-> pas de nouvelle version inutile
```

mais :

```text
ancien bulletin d'une section anglophone (ancien PDF français)
-> prochain publish produit un PDF anglais
-> nouvelle version créée
```
