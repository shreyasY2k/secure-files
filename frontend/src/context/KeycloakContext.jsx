// src/context/KeycloakContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import keycloak from '../services/keycloak';

const KeycloakContext = createContext(null);

export const KeycloakProvider = ({ children }) => {
    const [initialized, setInitialized] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userProfile, setUserProfile] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const initKeycloak = async () => {
            try {
                const authenticated = await keycloak.init({
                    onLoad: 'check-sso',
                    silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
                    pkceMethod: 'S256',
                    checkLoginIframe: false,
                    enableLogging: true,
                    useNonce: false,
                });

                setIsAuthenticated(authenticated);

                if (authenticated) {
                    // Set up token refresh
                    keycloak.onTokenExpired = () => {
                        keycloak.updateToken(30).catch(() => {
                            console.log('Token refresh failed; logging out');
                            keycloak.logout();
                        });
                    };
                }
                setInitialized(true);
            } catch (err) {
                setError(err);
                console.error('Failed to initialize Keycloak:', err);
            } finally {
                setIsLoading(false);
            }
        };

        initKeycloak();

        // Set up event listeners
        const refreshInterval = setInterval(() => {
            if (keycloak.authenticated) {
                keycloak.updateToken(70).catch(() => {
                    console.log('Token refresh failed; logging out');
                    keycloak.logout();
                });
            }
        }, 60000); // Refresh token every minute

        return () => {
            clearInterval(refreshInterval);
        };
    }, []);

    const login = () => keycloak.login();
    const logout = () => keycloak.logout();
    const hasRole = (role) => keycloak.hasRealmRole(role);
    const getToken = () => keycloak.token;

    const value = {
        initialized,
        isAuthenticated,
        userProfile,
        isLoading,
        error,
        login,
        logout,
        hasRole,
        getToken,
        keycloak // Expose the keycloak instance for advanced usage
    };

    return (
        <KeycloakContext.Provider value={value}>
            {children}
        </KeycloakContext.Provider>
    );
};

export const useKeycloak = () => {
    const context = useContext(KeycloakContext);
    if (!context) {
        throw new Error('useKeycloak must be used within a KeycloakProvider');
    }
    return context;
};