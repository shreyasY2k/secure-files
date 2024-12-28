# import requests
# import logging

# from django.conf import settings

# from typing import Optional, Dict, Any
# from ..core.keycloak_admin import KeycloakAdmin

# logger = logging.getLogger(__name__)

# class KeycloakError(Exception):
#     """Base exception for Keycloak operations"""
#     pass

# def get_keycloak_user_by_email(email: str) -> Optional[Dict[str, Any]]:
#     """Get a Keycloak user by email"""
#     try:
#         admin_token = KeycloakAdmin().get_keycloak_token()
#         headers = {
#             'Authorization': f'Bearer {admin_token}',
#             'Content-Type': 'application/json'
#         }

#         response = requests.get(
#             f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
#             headers=headers,
#             params={'email': email}
#         )
#         response.raise_for_status()
#         users = response.json()

#         if users:
#             return users[0]
#         return None
    
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Error getting Keycloak user by email: {str(e)}")
#         raise KeycloakError("Failed to get user by email") from e
#     except Exception as e:
#         logger.error(f"Unexpected error getting user by email: {str(e)}")
#         raise KeycloakError("Unexpected error getting user by email") from e

# # def create_temp_access_token(share_link) -> str:
# #     """
# #     Creates a temporary access token for a share link using Keycloak
# #     """
# #     try:
# #         admin_token = KeycloakAdmin.get_keycloak_token()
        
# #         # Generate a unique username for this share link
# #         temp_username = f"share_link_{uuid.uuid4()}"
        
# #         # Create user data with share link attributes
# #         user_data = {
# #             'username': temp_username,
# #             'email': f"{temp_username}@{settings.KEYCLOAK_REALM}.com",
# #             'enabled': True,
# #             'emailVerified': True,
# #             'attributes': {
# #                 'share_link_id': str(share_link.id),
# #                 'expires_at': share_link.expires_at.isoformat(),
# #                 'temporary': 'true'
# #             },
# #             'groups': [settings.KEYCLOAK_SHARE_LINK_GROUP],
# #             'realmRoles': ['share-link-access']
# #         }
        
# #         # Create the temporary user
# #         user_id = create_keycloak_user(user_data, admin_token)
        
# #         if not user_id:
# #             raise KeycloakError("Failed to create temporary user")

# #         # Generate token for this user
# #         token = generate_user_token(user_id, admin_token)
        
# #         # Schedule user cleanup
# #         schedule_user_cleanup(user_id, share_link.expires_at)
        
# #         return token
        
# #     except Exception as e:
# #         logger.error(f"Error creating temporary access token: {str(e)}")
# #         raise KeycloakError("Failed to create temporary access token") from e

# # def create_keycloak_user(user_data: Dict[str, Any], admin_token: str) -> Optional[str]:
# #     """Create a new user in Keycloak"""
# #     try:
# #         headers = {
# #             'Authorization': f'Bearer {admin_token}',
# #             'Content-Type': 'application/json'
# #         }
        
# #         response = requests.post(
# #             f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
# #             headers=headers,
# #             json=user_data
# #         )
# #         logger.info(f"Keycloak user creation response: {response.status_code}")
# #         logger.info(f"Keycloak user creation response: {response.text}")
# #         response.raise_for_status()
        
# #         # Get user ID from Location header
# #         user_id = response.headers['Location'].split('/')[-1]
# #         return user_id
        
# #     except requests.exceptions.RequestException as e:
# #         logger.error(f"Error creating Keycloak user: {str(e)}")
# #         return None

# # def generate_user_token(user_id: str, admin_token: str) -> str:
# #     """Generate a token for a specific user"""
# #     try:
# #         # Get user details
# #         headers = {
# #             'Authorization': f'Bearer {admin_token}',
# #             'Content-Type': 'application/json'
# #         }
        
# #         response = requests.get(
# #             f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}",
# #             headers=headers
# #         )
# #         response.raise_for_status()
# #         user_data = response.json()
        
# #         # Generate token
# #         token_url = (
# #             f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/"
# #             "protocol/openid-connect/token"
# #         )
        
# #         response = requests.post(
# #             token_url,
# #             data={
# #                 'username': 'admin',  # Using admin username from settings
# #                 'password': 'admin',  # Using admin password from settings
# #                 'grant_type': 'password',
# #                 'client_id': 'admin-cli' # Using the built-in admin-cli client
# #             }
# #         )
# #         logger.info(f"Keycloak token generation response: {response.status_code}")
# #         logger.info(f"Keycloak token generation response: {response.text}")
# #         response.raise_for_status()
# #         token_data = response.json()
        
# #         return token_data['access_token']
        
# #     except requests.exceptions.RequestException as e:
# #         logger.error(f"Error generating user token: {str(e)}")
# #         raise KeycloakError("Failed to generate user token") from e



# # def verify_temp_access_token(token: str) -> Optional[str]:
# #     """
# #     Verifies a temporary access token and returns the share_link_id if valid
# #     """
# #     try:
# #         introspect_endpoint = (
# #             f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/"
# #             "protocol/openid-connect/token/introspect"
# #         )
        
# #         response = requests.post(
# #             introspect_endpoint,
# #             data={
# #                 'token': token,
# #                 'client_id': settings.KEYCLOAK_CLIENT_ID,
# #                 'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
# #             }
# #         )
# #         response.raise_for_status()
# #         token_data = response.json()

# #         if not token_data.get('active', False):
# #             logger.warning(f"Inactive token attempted: {token}")
# #             return None

# #         # Extract and verify claims
# #         share_link_id = token_data.get('share_link_id')
# #         if not share_link_id:
# #             logger.warning(f"Token missing share_link_id claim: {token}")
# #             return None

# #         roles = token_data.get('realm_access', {}).get('roles', [])
# #         if 'share-link-access' not in roles:
# #             logger.warning(f"Token missing required role: {token}")
# #             return None

# #         return share_link_id

# #     except requests.exceptions.RequestException as e:
# #         logger.error(f"Error verifying token: {str(e)}")
# #         return None

# # def revoke_user_token(token: str) -> bool:
# #     """
# #     Revoke a user's token
# #     """
# #     try:
# #         admin_token = KeycloakAdmin.get_keycloak_token()
# #         headers = {
# #             'Authorization': f'Bearer {admin_token}',
# #             'Content-Type': 'application/json'
# #         }

# #         response = requests.post(
# #             f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/logout",
# #             headers=headers
# #         )
# #         response.raise_for_status()
# #         return True

# #     except Exception as e:
# #         logger.error(f"Error revoking token: {str(e)}")
# #         return False    

# # def schedule_user_cleanup(user_id: str, expires_at: datetime) -> None:
#     # """Schedule a user for cleanup when their access expires"""
#     # try:
#     #     expires_timestamp = expires_at.timestamp()
#     #     now = datetime.now(timezone.utc).timestamp()
#     #     ttl = int(expires_timestamp - now)
        
#     #     if ttl > 0:
#     #         cache.set(
#     #             f'cleanup_user_{user_id}',
#     #             user_id,
#     #             ttl
#     #         )
#     # except Exception as e:
#     #     logger.error(f"Error scheduling user cleanup: {str(e)}")

# # def cleanup_expired_users() -> None:
# #     """
# #     Cleanup task for expired temporary users
# #     Should be run periodically (e.g., via celery)
# #     """
# #     try:
# #         admin_token = KeycloakAdmin.get_keycloak_token()
# #         headers = {
# #             'Authorization': f'Bearer {admin_token}',
# #             'Content-Type': 'application/json'
# #         }

# #         # Get all users in share-link-users group
# #         response = requests.get(
# #             f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/groups/"
# #             f"{settings.KEYCLOAK_SHARE_LINK_GROUP}/members",
# #             headers=headers
# #         )
# #         response.raise_for_status()
# #         users = response.json()

# #         now = datetime.now(timezone.utc)

# #         for user in users:
# #             attributes = user.get('attributes', {})
# #             expires_at_str = attributes.get('expires_at', [None])[0]
            
# #             if expires_at_str:
# #                 expires_at = datetime.fromisoformat(expires_at_str)
# #                 if expires_at <= now:
# #                     # Delete expired user
# #                     requests.delete(
# #                         f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/"
# #                         f"users/{user['id']}",
# #                         headers=headers
# #                     )
# #                     logger.info(f"Deleted expired user: {user['id']}")

# #     except Exception as e:
# #         logger.error(f"Error cleaning up expired users: {str(e)}")

# # # def check_user_roles(token: str, required_roles: list) -> bool:
#     """
#     Check if a user has all the required roles
#     """
#     try:
#         # Verify token and get user roles
#         introspect_endpoint = (
#             f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/"
#             "protocol/openid-connect/token/introspect"
#         )
        
#         response = requests.post(
#             introspect_endpoint,
#             data={
#                 'token': token,
#                 'client_id': settings.KEYCLOAK_CLIENT_ID,
#                 'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
#             }
#         )
#         response.raise_for_status()
#         token_data = response.json()

#         if not token_data.get('active', False):
#             return False

#         # Get user roles
#         roles = token_data.get('realm_access', {}).get('roles', [])
        
#         # Check if user has all required roles
#         return all(role in roles for role in required_roles)

#     except Exception as e:
#         logger.error(f"Error checking user roles: {str(e)}")
#         return False