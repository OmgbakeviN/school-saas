# BE WISE School — GitHub + Docker + PostgreSQL

## Architecture

Local : React/Vite -> Django -> SQLite.

Serveur : Nginx Ubuntu/TLS -> `127.0.0.1:8088` -> frontend Nginx Docker -> Django/Gunicorn -> PostgreSQL Docker.

Le même `settings.py` garde SQLite tant que `DATABASE_URL` n'est pas défini. `.env.production` définit PostgreSQL uniquement sur le serveur.

## DNS

Créer deux enregistrements A vers l'IP du serveur :

```text
school.bewiseinnovation.com
*.school.bewiseinnovation.com
```

Le wildcard permet `slug.school.bewiseinnovation.com` pour chaque école.

## GitHub

Depuis la racine du projet local :

```bash
git init
git add .
git commit -m "Initial BE WISE School SaaS"
git branch -M main
git remote add origin git@github.com:VOTRE_ORG/bewise-school.git
git push -u origin main

git checkout -b develop
git push -u origin develop
```

Organisation équipe recommandée : branche par développeur/fonctionnalité -> PR vers `develop`; `main` est la branche déployée.

Ne jamais commiter `.env.production`.

## Serveur Ubuntu

```bash
cd /opt/bewise/apps
git clone git@github.com:VOTRE_ORG/bewise-school.git
cd bewise-school
cp .env.production.example .env.production
nano .env.production
```

Générer des secrets :

```bash
openssl rand -base64 48
openssl rand -hex 32
```

`POSTGRES_PASSWORD` et le mot de passe dans `DATABASE_URL` doivent correspondre.

## Docker

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Logs backend :

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

Le backend exécute `migrate` et `collectstatic` au démarrage.

## Nginx hôte

```bash
sudo apt update
sudo apt install -y nginx
sudo cp deploy/nginx/school.bewiseinnovation.com.conf /etc/nginx/sites-available/school.bewiseinnovation.com
sudo ln -s /etc/nginx/sites-available/school.bewiseinnovation.com /etc/nginx/sites-enabled/school.bewiseinnovation.com
```

## HTTPS wildcard

Pour `*.school.bewiseinnovation.com`, utilisez un certificat wildcard avec validation DNS-01. Exemple :

```bash
sudo certbot certonly --manual --preferred-challenges dns \
  -d school.bewiseinnovation.com \
  -d '*.school.bewiseinnovation.com'
```

Après émission du certificat :

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Pour le renouvellement automatique, préférez le plugin DNS de votre fournisseur de domaine.

## Quatre écoles de test

Exemple de profils :

```text
primaire-fr.school.bewiseinnovation.com
primaire-bilingue.school.bewiseinnovation.com
secondaire-fr.school.bewiseinnovation.com
secondaire-en.school.bewiseinnovation.com
```

Ce sont quatre tenants dans la même application, pas quatre containers. Cela teste réellement votre isolation multi-tenant.

## Exploitation

Déploiement :

```bash
cd /opt/bewise/apps/bewise-school
./scripts/deploy.sh
```

Tests :

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec backend python manage.py test
```

Swagger : `https://school.bewiseinnovation.com/api/docs/`

Admin : `https://school.bewiseinnovation.com/admin/`

Backup PostgreSQL :

```bash
./scripts/backup-db.sh
```

## SQLite local conservé

Dans `backend/.env` local, ne définissez pas `DATABASE_URL`. Exemple :

```env
DEBUG=True
SECRET_KEY=dev-only
ALLOWED_HOSTS=localhost,127.0.0.1,.localhost
CORS_ALLOW_ALL_ORIGINS=True
```

Le code actuel retombera alors automatiquement sur `backend/db.sqlite3`.
