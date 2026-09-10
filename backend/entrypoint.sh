#!/bin/sh
set -e
python - <<'PY'
import os, time
import psycopg
url = os.environ.get("DATABASE_URL", "")
if url.startswith("postgres"):
    for attempt in range(60):
        try:
            with psycopg.connect(url):
                print("PostgreSQL is ready.")
                break
        except Exception as exc:
            if attempt == 59: raise
            print(f"PostgreSQL not ready ({attempt + 1}/60): {exc}")
            time.sleep(2)
PY
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
