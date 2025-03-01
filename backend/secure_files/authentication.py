import base64
import requests
import jwt

from rest_framework import authentication
from rest_framework import exceptions

from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class KeycloakAuthentication(authentication.BaseAuthentication):
    def get_public_key(self):
        cached_key = cache.get('keycloak_public_key')
        if cached_key:
            return cached_key

        try:
            jwks_uri = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
            keys_response = requests.get(jwks_uri, verify=False)
            keys_response.raise_for_status()
            keys = keys_response.json()

            # Find the RSA signing key
            for key in keys['keys']:
                if key['use'] == 'sig' and key['kty'] == 'RSA':
                    # Construct PEM public key
                    n = base64.urlsafe_b64decode(key['n'] + '=' * (4 - len(key['n']) % 4))
                    e = base64.urlsafe_b64decode(key['e'] + '=' * (4 - len(key['e']) % 4))
                    
                    numbers = rsa.RSAPublicNumbers(
                        e=int.from_bytes(e, byteorder='big'),
                        n=int.from_bytes(n, byteorder='big')
                    )
                    public_key = numbers.public_key()
                    
                    pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    
                    # Cache the PEM key
                    cache.set('keycloak_public_key', pem, 3600)
                    return pem

            raise Exception("No suitable signing key found")
            
        except Exception as e:
            print(f"Error fetching public key: {str(e)}")
            raise exceptions.AuthenticationFailed(f'Could not fetch public key: {str(e)}')

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        # Skip Keycloak validation for share link downloads
        if request.path.startswith('/api/files/download/'):
            return None

        try:
            auth_parts = auth_header.split(' ')
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None

            token = auth_parts[1]
            public_key = self.get_public_key()

            try:
                decoded_token = jwt.decode(
                    token,
                    public_key,
                    algorithms=['RS256'],
                    options={
                        'verify_signature': True,
                        'verify_exp': True
                    }
                )
                
            except Exception as e:
                print(f"Token decode error: {str(e)}")
                raise exceptions.AuthenticationFailed(f'Token validation failed: {str(e)}')

            # Get or create user
            username = decoded_token.get('preferred_username', decoded_token.get('sub'))
            email = decoded_token.get('email', '')

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            user.token = decoded_token
            return (user, decoded_token)

        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed(str(e))