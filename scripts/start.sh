#!/usr/bin/env sh
set -e

python manage.py migrate --noinput
python manage.py sync_quiz
python manage.py seed_pitch_demo
exec uvicorn kivuko.asgi:application --host "0.0.0.0" --port "${PORT:-8000}"
