#!/bin/sh
set -e

mkdir -p /app/media

python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput || true
fi

if [ "$SEED_DEMO_DATA" = "True" ]; then
    python manage.py seed_demo_data
fi

python manage.py runserver 0.0.0.0:8011
