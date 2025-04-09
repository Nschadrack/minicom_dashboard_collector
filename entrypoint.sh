#!/bin/sh

# Get the number of CPUs
NUM_CPUS=$(nproc)

# Calculate the number of workers (2 * CPUs + 1)
NUM_WORKERS=$((NUM_CPUS + 4))

python manage.py makemigrations --no-input


python manage.py migrate --no-input --verbosity 3

python manage.py showmigrations

python manage.py collectstatic --no-input

gunicorn --workers $NUM_WORKERS --bind 0.0.0.0:8000 --timeout 300 mminicom_dashboard.wsgi:application

python manage.py qcluster # start django task queue
# python manage.py runserver 0.0.0.0:8000
