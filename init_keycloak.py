import os
import json
import time
import requests
import logging
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KeycloakInitializer:
    def __init__(self):
        self.keycloak_url = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080")
        self.keycloak_management_url = os.getenv(
            "KEYCLOAK_MANAGEMENT_URL", "http://keycloak:9000/health/ready"
        )
        self.admin_username = os.environ.get("KEYCLOAK_ADMIN", "admin")
        self.admin_password = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin")
        self.frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3003")
        self.token = None

        # User credentials
        self.secure_files_admin = {
            "username": os.environ.get("SECURE_FILES_ADMIN_USERNAME", "admin"),
            "password": os.environ.get("SECURE_FILES_ADMIN_PASSWORD", "Admin@123456"),
            "email": os.environ.get(
                "SECURE_FILES_ADMIN_EMAIL", "admin@securefile.local"
            ),
            "firstName": "Admin",
            "lastName": "User",
        }

        self.secure_files_user = {
            "username": os.environ.get("SECURE_FILES_USER_USERNAME", "user"),
            "password": os.environ.get("SECURE_FILES_USER_PASSWORD", "User@123456"),
            "email": os.environ.get("SECURE_FILES_USER_EMAIL", "user@securefile.local"),
            "firstName": "Regular",
            "lastName": "User",
        }

    def _make_request(self, method, endpoint, data=None, params=None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{self.keycloak_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            verify=False,
        )
        return response

    def wait_for_keycloak(self):
        logger.info("Waiting for Keycloak to be ready...")
        while True:
            try:
                response = requests.get(f"{self.keycloak_url}/realms/master/.well-known/openid-configuration", verify=False)
                logger.info(f"Keycloak status code: {response.status_code}")
                if response.status_code == 200 or response.status_code == 201:
                    logger.info("Keycloak is ready")
                    return
            except Exception as e:
                logger.error(f"Keycloak not ready: {str(e)}")
                logger.info("Keycloak not ready, waiting...")
                time.sleep(15)

    def get_token(self):
        logger.info("Getting admin token...")
        try:
            response = requests.post(
                f"{self.keycloak_url}/realms/master/protocol/openid-connect/token",
                data={
                    "username": self.admin_username,
                    "password": self.admin_password,
                    "grant_type": "password",
                    "client_id": "admin-cli",
                },
                verify=False,
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
            logger.info("Successfully obtained admin token")
        except Exception as e:
            logger.error(f"Failed to get token: {str(e)}")
            raise

    def import_realm(self):
        logger.info("Importing realm from JSON...")
        try:
            # Load realm configuration
            with open("realm-config.json", "r") as f:
                realm_config = json.load(f)

            # Create realm
            response = self._make_request("POST", "/admin/realms", realm_config)
            if response.status_code in [201, 409]:
                logger.info("Realm imported successfully")
            else:
                logger.error(f"Failed to import realm: {response.text}")
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to import realm: {str(e)}")
            raise

    def create_user(self, user_data, role_name):
        logger.info(f"Creating user {user_data['username']}...")
        user_config = {
            "username": user_data["username"],
            "enabled": True,
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "email": user_data["email"],
            "emailVerified": True,
            "credentials": [
                {"type": "password", "value": user_data["password"], "temporary": False}
            ],
            "requiredActions": ["CONFIGURE_TOTP"],
        }

        try:
            # Create user
            response = self._make_request(
                "POST", "/admin/realms/secure-files/users", user_config
            )
            if response.status_code == 201:
                logger.info(f"User {user_data['username']} created")
            elif response.status_code == 409:
                logger.info(f"User {user_data['username']} already exists")
            else:
                response.raise_for_status()

            # Get user ID
            response = self._make_request(
                "GET",
                "/admin/realms/secure-files/users",
                params={"username": user_data["username"]},
            )
            response.raise_for_status()
            user_id = response.json()[0]["id"]

            # Get role
            response = self._make_request(
                "GET", f"/admin/realms/secure-files/roles/{role_name}"
            )
            response.raise_for_status()
            role = response.json()

            # Assign role
            role_mapping = [
                {
                    "id": role["id"],
                    "name": role["name"],
                    "composite": False,
                    "clientRole": False,
                    "containerId": "secure-files",
                }
            ]

            response = self._make_request(
                "POST",
                f"/admin/realms/secure-files/users/{user_id}/role-mappings/realm",
                role_mapping,
            )
            response.raise_for_status()
            logger.info(f"Role {role_name} assigned to user {user_data['username']}")

        except Exception as e:
            logger.error(
                f"Failed to create/setup user {user_data['username']}: {str(e)}"
            )
            raise

    def check_realm_exists(self):
        response = self._make_request("GET", "/admin/realms/secure-files")
        return response.status_code == 200

    def run(self):
        try:
            self.wait_for_keycloak()
            self.get_token()
            if self.check_realm_exists():
                logger.info("Realm already exists")
            else:
                self.import_realm()
                self.create_user(self.secure_files_admin, "admin")
                self.create_user(self.secure_files_user, "user")
            logger.info("Keycloak initialization completed successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise


if __name__ == "__main__":
    initializer = KeycloakInitializer()
    initializer.run()
