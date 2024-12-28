#!/bin/bash
# backend/entrypoint.sh

echo "Applying database migrations..."
python manage.py migrate

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000