#!/bin/sh

python manage.py makemigrations --no-input


python manage.py migrate --no-input --verbosity 3

python manage.py showmigrations

python manage.py collectstatic --no-input

gunicorn minicom_dashboard.wsgi:application --bind 0.0.0.0:8000
# python manage.py runserver 0.0.0.0:8000