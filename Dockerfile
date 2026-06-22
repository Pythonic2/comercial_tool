FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_ENV=development python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["sh", "-c", "exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers ${GUNICORN_WORKERS:-1} --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile -"]
