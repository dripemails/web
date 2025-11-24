#!/bin/bash
NAME="dripemails"                      # Name of the application
DJANGODIR=/home/dripemails/web       # Path to Django project
VENV=${VENV:-/home/dripemails/dripemails}  # Virtual environment path (default: /home/dripemails/web/dripemails)
SOCKFILE=/tmp/gunicorn.sock      # Path to the socket file
USER=dripemails                                # User to run the process
GROUP=dripemails                              # Group to run the process
NUM_WORKERS=12                                # Number of worker processes
DJANGO_SETTINGS_MODULE=dripemails.live  # Django settings file
DJANGO_WSGI_MODULE=dripemails.wsgi          # Django WSGI module

export VENV=/home/dripemails/dripemails

# Change to project directory (required for Python to find modules)
cd $DJANGODIR

# Activate virtual environment if it exists
if [ -f "$VENV/bin/activate" ]; then
    source $VENV/bin/activate
fi

# Use gunicorn from virtual environment if available, otherwise use system gunicorn
GUNICORN_CMD=${GUNICORN_CMD:-$VENV/bin/gunicorn}
if [ ! -f "$GUNICORN_CMD" ]; then
    # Fallback to system gunicorn if venv doesn't have it
    GUNICORN_CMD=gunicorn
fi

# Set Python path explicitly (required for Django to find modules)
export PYTHONPATH=$DJANGODIR

# Set Django settings module
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Set locale environment variables
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

# Ensure locale directory exists and is accessible
export LOCALE_PATHS=$DJANGODIR/locale

# Run Gunicorn
# Note: Using TCP socket (127.0.0.1:9000) for nginx proxy
# Alternative: Use Unix socket by uncommenting the unix socket line and commenting the TCP bind
exec $GUNICORN_CMD \
    --user=$USER \
    --group=$GROUP \
    --workers=$NUM_WORKERS \
    --bind=0.0.0.0:8005 \
    --log-level=debug \
    --log-file=- \
    $DJANGO_WSGI_MODULE:application
    # Alternative Unix socket: --bind=unix:$SOCKFILE
