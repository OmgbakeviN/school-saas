# BE WISE School — Profils personnes, filtres élèves & photos élèves

## Objectif

Cette amélioration rend l'espace **Personnes & inscriptions** plus exploitable au quotidien et prépare les fiches élèves/bulletins à l'utilisation de photos d'identité facultatives.

## Profils

Chaque carte Élève, Enseignant et Parent/Tuteur possède maintenant une action **Voir le profil**.

Le profil élève présente notamment :
- identité et matricule ;
- informations personnelles et contacts ;
- inscription active ;
- photo si disponible ;
- parents/tuteurs liés avec type de relation et parent principal.

Le profil parent/tuteur présente notamment :
- coordonnées et profession ;
- langue préférée ;
- compte utilisateur lié lorsqu'il existe ;
- tous les enfants liés, avec matricule, relation, classe et année active.

Le profil enseignant affiche ses informations professionnelles et son compte de connexion lié.

## Recherche et filtres élèves

La recherche élève couvre désormais le nom, matricule, téléphone, email, classe ainsi que le nom/téléphone des parents liés.

Filtres UI :
- classe ;
- statut ;
- sexe ;
- avec photo / sans photo.

L'API élèves accepte aussi `gender` et `has_photo`, et la recherche serveur sait retrouver un élève via un parent lié.

## Photo élève

Route dédiée :

```http
POST /api/people/students/{id}/photo/
PUT /api/people/students/{id}/photo/
DELETE /api/people/students/{id}/photo/
```

Upload multipart :

```text
photo=<fichier>
```

Formats : JPG, PNG, WEBP.

Traitement automatique côté backend :
1. limite de fichier source : 15 Mo ;
2. limite de sécurité : 40 mégapixels ;
3. correction de l'orientation EXIF ;
4. conversion en RGB ;
5. redimensionnement proportionnel, maximum 900 × 900 ;
6. conversion WEBP ;
7. compression adaptative (qualité 82 → 76 → 70) avec cible d'environ 500 Ko ;
8. réduction supplémentaire à 720 px si nécessaire.

L'image originale lourde n'est donc pas conservée comme photo de profil.

## Photo dans le bulletin

Dans **Bulletins > Modèles A4**, une nouvelle option apparaît :

```text
Afficher la photo de l'élève / Show student photo
```

Elle est désactivée par défaut.

Quand elle est activée et que l'élève possède une photo :
- la photo est placée à droite du bloc d'identité ;
- le moteur conserve la contrainte d'une seule page A4 ;
- le snapshot enregistre l'empreinte SHA-256 de la photo utilisée ;
- une modification de photo peut donc produire une nouvelle version officielle lors d'une republication.

Si l'option est désactivée, la photo n'influence pas le contenu versionné du bulletin.

## Migrations

```powershell
python manage.py migrate
```

Migrations de cette livraison :

```text
people.0002_student_photo
report_cards.0003_reportcardtemplate_student_photo
```

## Production : taille des uploads

Le backend accepte jusqu'à 15 Mo afin de pouvoir recevoir une photo haute définition avant compression.

Si le proxy Nginx renvoie `413 Request Entity Too Large`, ajouter une limite supérieure, par exemple :

```nginx
client_max_body_size 16M;
```

sur le virtual host qui reçoit `/api/`, puis recharger Nginx.

Les photos sont stockées dans `MEDIA_ROOT`. En production, elles utilisent donc le même mécanisme `/media/` que les logos et autres médias BE WISE.

## Validation réalisée sur la livraison

- syntaxe Python des fichiers modifiés : OK ;
- analyse syntaxique JSX/JS : OK ;
- structure des migrations : vérifiée statiquement ;
- génération ReportLab d'un bulletin avec photo : effectuée ;
- rendu obtenu : 1 page A4 et inspection visuelle satisfaisante.

L'environnement de génération ne contient pas Django ; `manage.py check` et la suite de tests Django complète n'ont donc pas été exécutés ici. Ils doivent être lancés dans le `.venv` du projet.
