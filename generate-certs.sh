#!/bin/bash
# generate-certs.sh

# Create cert directories for each service
mkdir -p ./frontend/certs
mkdir -p ./backend/certs
mkdir -p ./keycloak/certs

# Generate CA key and certificate
openssl genpkey -algorithm RSA -out ./frontend/certs/ca.key
openssl req -x509 -new -nodes -key ./frontend/certs/ca.key -sha256 -days 1825 -out ./frontend/certs/ca.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=Local CA"

# Copy CA cert to other services
cp ./frontend/certs/ca.crt ./backend/certs/
cp ./frontend/certs/ca.crt ./keycloak/certs/

# Function to generate certificate for a service
generate_cert() {
    local SERVICE=$1
    local DOMAIN=$2
    local SERVICE_DIR="./${SERVICE}/certs"

    # Generate private key
    openssl genpkey -algorithm RSA -out "${SERVICE_DIR}/${SERVICE}.key"

    # Create CSR config
    cat > "${SERVICE_DIR}/${SERVICE}.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = req_ext

[dn]
C = US
ST = State
L = City
O = Organization
CN = ${DOMAIN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = localhost
EOF

    # Generate CSR
    openssl req -new -key "${SERVICE_DIR}/${SERVICE}.key" -out "${SERVICE_DIR}/${SERVICE}.csr" -config "${SERVICE_DIR}/${SERVICE}.conf"

    # Generate certificate
    openssl x509 -req -in "${SERVICE_DIR}/${SERVICE}.csr" \
        -CA ./frontend/certs/ca.crt -CAkey ./frontend/certs/ca.key -CAcreateserial \
        -out "${SERVICE_DIR}/${SERVICE}.crt" -days 825 -sha256 \
        -extensions req_ext -extfile "${SERVICE_DIR}/${SERVICE}.conf"

    # Create combined PEM file for services that need it
    cat "${SERVICE_DIR}/${SERVICE}.crt" "${SERVICE_DIR}/${SERVICE}.key" > "${SERVICE_DIR}/${SERVICE}.pem"

    # Clean up CSR and config
    rm "${SERVICE_DIR}/${SERVICE}.csr" "${SERVICE_DIR}/${SERVICE}.conf"
}

# Generate certificates for each service
generate_cert "frontend" "localhost"
generate_cert "backend" "localhost"
generate_cert "keycloak" "localhost"

echo "Certificates generated successfully"