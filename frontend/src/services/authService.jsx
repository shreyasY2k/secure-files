// src/services/authService.js
export const checkMFAStatus = async (keycloak) => {
    try {
        const token = keycloak.token;
        const response = await fetch(
            `${keycloak.authServerUrl}/realms/${keycloak.realm}/users/${keycloak.tokenParsed.sub}/credentials`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (response.ok) {
            const credentials = await response.json();
            return credentials.some(cred => cred.type === 'otp');
        }
        return false;
    } catch (error) {
        console.error('Error checking MFA status:', error);
        return false;
    }
};