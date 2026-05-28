#!/bin/sh
set -e

mkdir -p /app/data /app/media

if [ ! -f /app/data/db.sqlite3 ] && [ -f /app/db.sqlite3 ]; then
    cp /app/db.sqlite3 /app/data/db.sqlite3
fi

python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput || true
fi

if [ "$SEED_DEMO_DATA" = "True" ]; then
    python manage.py seed_demo_data
fi

python manage.py runserver 0.0.0.0:8011
