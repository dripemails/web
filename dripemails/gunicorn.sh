#!/bin/bash
NAME="dripemails"                      # Name of the application
DJANGODIR=/home/dripemails/web       # Path to Django project
SOCKFILE=/tmp/gunicorn.sock      # Path to the socket file
USER=dripemails                                # User to run the process
GROUP=dripemails                              # Group to run the process
NUM_WORKERS=12                                # Number of worker processes
DJANGO_SETTINGS_MODULE=live  # Django settings file
DJANGO_WSGI_MODULE=wsgi          # Django WSGI module

cd $DJANGODIR
#source /path/to/your/virtualenv/bin/activate  # Activate virtual environment
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Set locale environment variables
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

# Ensure locale directory exists and is accessible
export LOCALE_PATHS=$DJANGODIR/locale

exec gunicorn --user=$USER --group=$GROUP --workers=$NUM_WORKERS --bind=127.0.0.1:9000 --log-level=debug --log-file=- $># --bind=unix:$SOCKFILE
