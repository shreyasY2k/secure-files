import requests
import logging

from django.conf import settings
from django.core.cache import cache

from datetime import timedelta

class KeycloakError(Exception):
    """Base exception for Keycloak operations"""
    pass

logger = logging.getLogger(__name__)

class KeycloakAdmin:
    def __init__(self):
        self.base_url = f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}"
        self.token = cache.get('keycloak_admin_token', None)

    def get_keycloak_token(self) :
        """Get admin token from Keycloak for server-side operations"""
        cache_key = 'keycloak_admin_token'
        cached_token = cache.get(cache_key)

        if cached_token:
            return cached_token

        try:
            # Use the /auth endpoint with admin credentials
            token_url = f"{settings.KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
            response = requests.post(
                token_url,
                data={
                    'username': settings.KEYCLOAK_ADMIN_USER,  # Using admin user from settings
                    'password': settings.KEYCLOAK_ADMIN_PASSWORD,  # Using admin password from settings
                    'grant_type': 'password',
                    'client_id': 'admin-cli'  # Using the built-in admin-cli client
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                verify=False  # Disable SSL verification
            )

            if response.status_code != 200:
                logger.error(f"Failed to get admin token. Status: {response.status_code}, Response: {response.text}")
                raise KeycloakError(f"Failed to obtain admin token. Status: {response.status_code}")

            token_data = response.json()

            # Cache the token for slightly less than its expiry time
            cache.set(
                cache_key,
                token_data['access_token'],
                token_data['expires_in'] - 60
            )
            self.token = token_data['access_token']

            logger.info("Successfully obtained Keycloak admin token")
            return token_data['access_token']

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Keycloak admin token: {str(e)}")
            raise KeycloakError("Failed to obtain admin token") from e
        except Exception as e:
            logger.error(f"Unexpected error getting admin token: {str(e)}")
            raise KeycloakError("Unexpected error obtaining admin token") from e
    
    def _get_headers(self):
        token = self.get_keycloak_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def create_user(self, user_data, role="user"):
        """Create a new user in Keycloak with specified role"""
        try:
            token = self.get_keycloak_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            # Create user in Keycloak
            user_payload = {
                'username': user_data['username'],
                'email': user_data['email'],
                'enabled': True,
                'emailVerified': False,
                'credentials': [{
                    'type': 'password',
                    'value': user_data['password'],
                    'temporary': False
                }],
                'realmRoles': [role]  # Assign role
            }

            # Create user
            response = requests.post(
                f"{self.base_url}/users",
                headers=headers,
                json=user_payload,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()

            # Get user ID from response
            user_id = response.headers['Location'].split('/')[-1]

            # Get role ID
            role_response = requests.get(
                f"{self.base_url}/roles/{role}",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            role_response.raise_for_status()
            role_data = role_response.json()

            # Assign role to user
            role_assignment = [{
                'id': role_data['id'],
                'name': role
            }]
            requests.post(
                f"{self.base_url}/users/{user_id}/role-mappings/realm",
                headers=headers,
                json=role_assignment,
                verify=False  # Disable SSL verification
            )

            return user_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak user creation error: {str(e)}")
            raise KeycloakError("Failed to create user in Keycloak")

    def delete_user(self, user_id):
        """Delete a user from Keycloak"""
        try:
            token = self.get_keycloak_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.delete(
                f"{self.base_url}/users/{user_id}",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak user deletion error: {str(e)}")
            raise KeycloakError("Failed to delete user from Keycloak")

    def get_user_id_by_username(self, username):
        """Get Keycloak user ID by username"""
        try:
            token = self.get_keycloak_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.base_url}/users?username={username}&exact=true",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            users = response.json()
            
            return users[0]['id'] if users else None

        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak user lookup error: {str(e)}")
            raise KeycloakError("Failed to lookup user in Keycloak")
        
    def get_all_users(self):
        """Get all users from Keycloak"""
        try:
            token = self.get_keycloak_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.base_url}/users",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak user lookup error: {str(e)}")
            raise KeycloakError("Failed to lookup user in Keycloak")
        
    def get_users_count(self):
        """Get total number of users"""
        try:
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/users/count",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user count: {str(e)}")
            raise KeycloakError("Failed to get user count")

    def get_active_users_count(self):
        """Get count of active users in last 30 days"""
        try:
            all_users = self.get_all_users(brief=True)
            thirty_days_ago = int((timezone.now() - timedelta(days=30)).timestamp() * 1000)
            
            active_users = [
                user for user in all_users
                if user.get('lastLogin', 0) > thirty_days_ago
            ]
            
            return len(active_users)
        except Exception as e:
            logger.error(f"Error getting active users count: {str(e)}")
            raise KeycloakError("Failed to get active users count")

    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        try:
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/users/{user_id}",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise KeycloakError(f"Failed to get user with ID {user_id}")

    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            headers = self._get_headers()
            params = {'email': email, 'exact': 'true'}
            
            response = requests.get(
                f"{self.base_url}/users",
                headers=headers,
                params=params,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            users = response.json()
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise KeycloakError(f"Failed to get user with email {email}")


    def get_user_roles(self, user_id):
        """Get roles assigned to a user"""
        try:
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/users/{user_id}/role-mappings/realm",
                headers=headers,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Error getting user roles: {str(e)}")
            raise KeycloakError("Failed to get user roles")
        
    def update_user_status(self, user_id, enabled):
        """Update user status"""
        try:
            headers = self._get_headers()
            response = requests.put(
                f"{self.base_url}/users/{user_id}",
                headers=headers,
                json={'enabled': enabled},
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error updating user status: {str(e)}")
            raise KeycloakError("Failed to update user status")