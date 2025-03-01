#!/bin/sh

# Directory for certificates
mkdir -p /certs

# Create config file
cat > /certs/certificate.conf << EOF
[req]
prompt = no
default_md = sha256
x509_extensions = v3_req
distinguished_name = dn

[dn]
C = IN
ST = Karnataka
L = Bangalore
O = ShreyasMkTech
CN = localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment, keyAgreement
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate certificates if they don't exist
if [ ! -f /certs/localhost.crt ]; then
    openssl genrsa -out /certs/localhost.key 2048
    openssl req -x509 -new -nodes \
        -key /certs/localhost.key \
        -sha256 -days 365 \
        -out /certs/localhost.crt \
        -config /certs/certificate.conf
    
    echo "Certificates generated successfully"
else
    echo "Certificates already exist"
fi

# Set proper permissions
chmod 644 /certs/localhost.crt
chmod 600 /certs/localhost.key