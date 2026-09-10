# Livraison HOTFIX 03.1.1

Extraire directement à la racine du projet.

Aucune migration n'est nécessaire.

Exemple :

```powershell
.venv\Scripts\Activate.ps1
cd backend
python manage.py seed_school_demo --school mon-ecole --reset
```

Valeurs par défaut :

```text
120 élèves
20 enseignants
~96 parents/tuteurs
```
