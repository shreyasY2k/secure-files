# backend/Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    file \
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
    && chmod -R 777 /app

# Copy project files
COPY . .

# Final permission adjustments
RUN chmod -R 777 /app/logs

# Command to run
ENTRYPOINT ["./entrypoint.sh"]