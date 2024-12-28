import logging

from rest_framework import permissions

logger = logging.getLogger(__name__)

class HasKeycloakRole(permissions.BasePermission):
    """
    Permission check for specific Keycloak roles.
    """
    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []
        logger.info(f"Initializing HasKeycloakRole with required roles: {self.required_roles}")

    def has_permission(self, request, view):
        logger.info("\n=== Keycloak Role Permission Check ===")
        logger.info(f"Required roles: {self.required_roles}")
        
        # Check authentication
        if not request.user.is_authenticated:
            logger.info("User is not authenticated")
            return False

        # Get token data
        token = getattr(request.user, 'token', None)
        logger.info(f"Full token content: {token}")
        
        if not token:
            logger.info("No token found on user object")
            return False

        # Extract roles from different possible locations in the token
        realm_roles = token.get('realm_access', {}).get('roles', [])
        scope = token.get('scope', '').split()
        
        logger.info(f"Realm roles: {realm_roles}")
        logger.info(f"Scopes: {scope}")

        # Check if user has any of the required roles
        for required_role in self.required_roles:
            if (required_role in realm_roles or 
                required_role in scope):
                logger.info(f"Found required role: {required_role}")
                return True

        logger.info("No required roles found")
        return False

    def __call__(self):
        return self