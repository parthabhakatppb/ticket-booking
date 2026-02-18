#!/usr/bin/env sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

./wait-for-it.sh "${DB_HOST}:${DB_PORT}" -- python manage.py migrate --noinput

exec python manage.py runserver 0.0.0.0:8000
