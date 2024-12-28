#!/bin/bash
# init-keycloak.sh

# Wait for Keycloak to be ready
until curl -s -k https://keycloak:8443/health/ready; do
    echo 'Waiting for Keycloak...'
    sleep 5
done

# Login to get admin token
TOKEN=$(curl -k -X POST https://keycloak:8443/realms/master/protocol/openid-connect/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${KEYCLOAK_ADMIN}" \
    -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    | jq -r '.access_token')

# Create realm
curl -k -X POST https://keycloak:8443/admin/realms \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "realm": "secure-files",
        "enabled": true,
        "registrationAllowed": true,
        "registrationEmailAsUsername": false,
        "verifyEmail": false,
        "loginWithEmailAllowed": false,
        "duplicateEmailsAllowed": false,
        "resetPasswordAllowed": true,
        "editUsernameAllowed": false,
        "bruteForceProtected": true,
        "passwordPolicy": "length(8) and upperCase(1) and lowerCase(1) and digits(1) and specialChars(1)",
        "requiredActions": ["CONFIGURE_TOTP"],
        "otpPolicyType": "totp",
        "otpPolicyAlgorithm": "HmacSHA1",
        "otpPolicyInitialCounter": 0,
        "otpPolicyDigits": 6,
        "otpPolicyLookAheadWindow": 1,
        "otpPolicyPeriod": 30,
        "browserSecurityHeaders": {
            "contentSecurityPolicy": "frame-src self; frame-ancestors self; object-src none;",
            "xFrameOptions": "SAMEORIGIN"
        }
    }'

# Create admin role
curl -k -X POST https://keycloak:8443/admin/realms/secure-files/roles \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "admin",
        "description": "Administrator role"
    }'

# Create user role
curl -k -X POST https://keycloak:8443/admin/realms/secure-files/roles \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "user",
        "description": "Standard user role"
    }'

# Create secure-files-client
curl -k -X POST https://keycloak:8443/admin/realms/secure-files/clients \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "secure-files-client",
        "enabled": true,
        "publicClient": true,
        "standardFlowEnabled": true,
        "directAccessGrantsEnabled": true,
        "implicitFlowEnabled": false,
        "serviceAccountsEnabled": false,
        "authorizationServicesEnabled": false,
        "redirectUris": ["'"${FRONTEND_URL}/*"'"],
        "webOrigins": ["'"${FRONTEND_URL}"'"],
        "attributes": {
            "post.logout.redirect.uris": "'"${FRONTEND_URL}/*"'",
            "pkce.code.challenge.method": "S256"
        },
        "protocol": "openid-connect",
        "defaultClientScopes": [
            "web-origins",
            "acr",
            "profile",
            "roles",
            "email"
        ]
    }'

# Configure Required Action for TOTP
curl -k -X PUT https://keycloak:8443/admin/realms/secure-files/authentication/required-actions/CONFIGURE_TOTP \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "alias": "CONFIGURE_TOTP",
        "name": "Configure OTP",
        "providerId": "CONFIGURE_TOTP",
        "enabled": true,
        "defaultAction": true,
        "priority": 10,
        "config": {}
    }'

# Create admin user
ADMIN_USER_ID=$(curl -k -X POST https://keycloak:8443/admin/realms/secure-files/users \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "'"${SECURE_FILES_ADMIN_USERNAME}"'",
        "enabled": true,
        "firstName": "Admin",
        "lastName": "User",
        "email": "'"${SECURE_FILES_ADMIN_EMAIL}"'",
        "emailVerified": true,
        "credentials": [{
            "type": "password",
            "value": "'"${SECURE_FILES_ADMIN_PASSWORD}"'",
            "temporary": false
        }],
        "requiredActions": ["CONFIGURE_TOTP"]
    }' \
    --write-out '%{http_code}' --silent --output /dev/null)

# Get admin user ID
ADMIN_USER_ID=$(curl -k -X GET "https://keycloak:8443/admin/realms/secure-files/users?username=${SECURE_FILES_ADMIN_USERNAME}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" | jq -r '.[0].id')

# Assign admin role to admin user
curl -k -X POST https://keycloak:8443/admin/realms/secure-files/users/${ADMIN_USER_ID}/role-mappings/realm \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '[{
        "name": "admin",
        "composite": false,
        "clientRole": false,
        "containerId": "secure-files"
    }]'

# Create regular user
curl -k -X POST https://keycloak:8443/admin/realms/secure-files/users \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "'"${SECURE_FILES_USER_USERNAME}"'",
        "enabled": true,
        "firstName": "Regular",
        "lastName": "User",
        "email": "'"${SECURE_FILES_USER_EMAIL}"'",
        "emailVerified": true,
        "credentials": [{
            "type": "password",
            "value": "'"${SECURE_FILES_USER_PASSWORD}"'",
            "temporary": false
        }],
        "requiredActions": ["CONFIGURE_TOTP"]
    }'

# Get regular user ID
USER_ID=$(curl -k -X GET "https://keycloak:8443/admin/realms/secure-files/users?username=${SECURE_FILES_USER_USERNAME}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" | jq -r '.[0].id')

# Assign user role to regular user
curl -k -X POST https://keycloak:8443/admin/realms/secure-files/users/${USER_ID}/role-mappings/realm \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '[{
        "name": "user",
        "composite": false,
        "clientRole": false,
        "containerId": "secure-files"
    }]'

echo "Keycloak initialization completed"