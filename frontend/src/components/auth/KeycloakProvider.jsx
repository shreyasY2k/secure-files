// src/components/auth/KeycloakProvider.jsx
import React from 'react';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import keycloak from '../../services/keycloak';

const KeycloakProvider = ({ children }) => {
    const handleEvent = (event, error) => {
        console.log('Keycloak event:', event);
        if (error) {
            console.error('Keycloak error:', error);
        }
    };

    const loadingComponent = (
        <div className="min-h-screen flex items-center justify-center">
            <div className="text-2xl text-gray-600">Loading...</div>
        </div>
    );

    return (
        <ReactKeycloakProvider
            authClient={keycloak}
            initOptions={{
                onLoad: 'check-sso',
                checkLoginIframe: false,
                pkceMethod: 'S256'
            }}
            onEvent={handleEvent}
            LoadingComponent={loadingComponent}
        >
            {children}
        </ReactKeycloakProvider>
    );
};

export default KeycloakProvider;