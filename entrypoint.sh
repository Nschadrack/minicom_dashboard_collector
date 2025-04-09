#!/bin/sh

# Load the .env file
set -a  # Automatically export all variables
source .env
set +a

python manage.py makemigrations --no-input


python manage.py migrate --no-input --verbosity 3

python manage.py showmigrations

python manage.py collectstatic --no-input

gunicorn minicom_dashboard.wsgi:application --bind 0.0.0.0:8000 --timeout "$GUNICORN_TIMEOUT"
# python manage.py runserver 0.0.0.0:8000
