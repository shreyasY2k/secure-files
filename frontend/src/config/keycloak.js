// src/config/keycloak.js
import Keycloak from "keycloak-js";

const keycloakConfig = {
    url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8013',
    realm: import.meta.env.VITE_KEYCLOAK_REALM || 'secure-files',
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'secure-files-client'
};

const keycloak = new Keycloak(keycloakConfig);

export default keycloak;