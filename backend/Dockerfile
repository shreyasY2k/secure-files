FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHTTPSVERIFY=0

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libmagic1 \
        file \
        netcat-traditional \
        curl \
        gunicorn \
        openssl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/media \
    /app/static \
    /app/staticfiles \
    /app/templates \
    /app/templates/admin \
    /app/certs \
    && chmod -R 777 /app

# Copy project files
COPY . .

# Final permission adjustments
RUN chmod -R 777 /app/logs

EXPOSE 3002

# Start command with all initialization steps
CMD set -e \
    && echo "Setting up directories..." \
    && mkdir -p /app/logs /app/media /app/static /app/staticfiles /app/templates \
    && chmod -R 777 /app/logs /app/media \
    && echo "Waiting for PostgreSQL..." \
    && while ! nc -z db 5432; do sleep 1; done \
    && echo "PostgreSQL is up and running!" \
    && echo "Running database migrations..." \
    && python manage.py makemigrations --noinput \
    && python manage.py migrate --noinput \
    && echo "Collecting static files..." \
    && python manage.py collectstatic --noinput \
    && echo "Starting Gunicorn server..." \
    && exec gunicorn secure_files.wsgi:application \
        --bind 0.0.0.0:3002 \
        --workers 2 \
        --timeout 120