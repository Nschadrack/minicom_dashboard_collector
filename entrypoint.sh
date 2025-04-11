#!/bin/sh

# Get the number of CPUs
NUM_CPUS=$(nproc)

# Calculate the number of workers (2 * CPUs + 1)
NUM_WORKERS=$((NUM_CPUS + 4))

python manage.py makemigrations --no-input


python manage.py migrate --no-input --verbosity 3

python manage.py showmigrations

python manage.py collectstatic --no-input

python manage.py process_tasks --duration 180 # background tasks queue and release database locks every 180 seconds

# Then start the Gunicorn server
gunicorn --workers $NUM_WORKERS --bind 0.0.0.0:8000 --timeout 300 minicom_dashboard.wsgi:application

# python manage.py runserver 0.0.0.0:8000
