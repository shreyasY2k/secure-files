import React, { useEffect } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { useNavigate } from 'react-router-dom';
import { Loader } from 'lucide-react';

const LandingPage = () => {
    const { keycloak, initialized } = useKeycloak();
    const navigate = useNavigate();

    useEffect(() => {
        if (initialized) {
            if (keycloak.authenticated) {
                navigate('/dashboard');
            } else {
                keycloak.login();
            }
        }
    }, [initialized, keycloak, navigate]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
                <Loader className="h-8 w-8 text-blue-600 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Redirecting to login...</p>
            </div>
        </div>
    );
};

export default LandingPage;