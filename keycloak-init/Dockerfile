FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-init.txt .
RUN pip install --no-cache-dir -r requirements-init.txt

COPY init_keycloak.py .
COPY realm-config.json .

CMD ["python", "init_keycloak.py"]