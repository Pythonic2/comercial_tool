#!/bin/sh
set -eu

case "${RUN_MIGRATIONS:-false}" in
    true|True|TRUE|1|yes|Yes|YES)
        if [ "${DJANGO_ENV:-}" != "production" ]; then
            echo "ERROR: RUN_MIGRATIONS requires DJANGO_ENV=production." >&2
            exit 1
        fi

        python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); from django.conf import settings; db = settings.DATABASES['default']; assert db['ENGINE'] == 'django.db.backends.postgresql', 'Migrations blocked: database is not PostgreSQL'; print('Migrations on PostgreSQL: {}/{}'.format(db['HOST'], db['NAME']))"
        python manage.py migrate --noinput
        ;;
esac

exec gunicorn core.wsgi:application --bind "0.0.0.0:${PORT:-8080}" --workers "${GUNICORN_WORKERS:-1}" --threads "${GUNICORN_THREADS:-4}" --timeout "${GUNICORN_TIMEOUT:-120}" --access-logfile - --error-logfile -
