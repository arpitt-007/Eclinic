#!/usr/bin/env bash
# Render build script: install deps, collect static files, migrate the database.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Create the admin account from DJANGO_SUPERUSER_* env vars (skipped if it already exists).
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --no-input || true
fi

# Load demo doctors/patient so the site isn't empty. Set SEED_DEMO=0 to disable.
if [ "${SEED_DEMO:-0}" = "1" ]; then
  python manage.py seed_demo
fi
