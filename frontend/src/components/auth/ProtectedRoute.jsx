import { useKeycloak } from '@react-keycloak/web';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredRoles = [] }) => {
    const { keycloak, initialized } = useKeycloak();

    if (!initialized) {
        return <div>Loading...</div>;
    }

    if (!keycloak.authenticated) {
        return <Navigate to="/" />;
    }

    if (requiredRoles.length > 0) {
        const hasRequiredRoles = requiredRoles.every(role =>
            keycloak.hasRealmRole(role)
        );

        if (!hasRequiredRoles) {
            return <div>Access Denied: Insufficient permissions</div>;
        }
    }

    return children;
};

export default ProtectedRoute;