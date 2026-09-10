# Application des fichiers

Copiez le contenu de cette archive à la racine de votre projet.

Puis remplacez votre `backend/config/settings.py` par le fichier fourni `backend/config.settings.py` (renommez-le en `settings.py` dans `backend/config/`).

Le `backend/requirements.txt` fourni ajoute Gunicorn et WhiteNoise aux dépendances existantes.

Le frontend Dockerfile suppose que votre projet local possède déjà son `package.json` et idéalement `package-lock.json`.
