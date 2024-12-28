import os

from base64 import b64encode, b64decode

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class FileEncryption:
    def __init__(self, key=None, iv=None):
        """Initialize with key and IV, or generate new ones"""
        self.key = key if key else os.urandom(32)  # 256-bit key
        self.iv = iv if iv else os.urandom(16)   # 128-bit IV for AES

    def encrypt(self, data):
        """
        Encrypt data using AES-256-GCM
        Returns: (encrypted_data, key, iv)
        """
        try:
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(self.iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Encrypt data
            encrypted_data = encryptor.update(data) + encryptor.finalize()

            # Return encrypted data with tag
            return {
                'encrypted_data': encrypted_data,
                'tag': encryptor.tag,
                'key': self.key,
                'iv': self.iv
            }
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data, tag):
        """
        Decrypt data using AES-256-GCM
        """
        try:
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(self.iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt data
            return decryptor.update(encrypted_data) + decryptor.finalize()
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")

    @staticmethod
    def encode_key(key):
        """Encode key to base64 for storage"""
        return b64encode(key).decode('utf-8')

    @staticmethod
    def decode_key(encoded_key):
        """Decode key from base64"""
        return b64decode(encoded_key.encode('utf-8'))

class EncryptionError(Exception):
    """Custom exception for encryption/decryption errors"""
    pass