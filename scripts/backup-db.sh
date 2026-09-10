#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${APP_DIR:-/opt/bewise/apps/bewise-school}"
BACKUP_DIR="${BACKUP_DIR:-/opt/bewise/backups/bewise-school}"
mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"
set -a; source .env.production; set +a
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="$BACKUP_DIR/postgres-$STAMP.sql.gz"
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"
echo "Backup created: $FILE"
