#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${APP_DIR:-/opt/bewise/apps/bewise-school}"
cd "$APP_DIR"
git fetch origin
git pull --ff-only origin main
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T backend python manage.py check --deploy
docker compose --env-file .env.production -f docker-compose.prod.yml ps
