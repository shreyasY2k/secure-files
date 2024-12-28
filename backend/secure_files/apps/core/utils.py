import base64

from cryptography.fernet import Fernet

def encrypt_file(file_data, key):
    fernet = Fernet(base64.urlsafe_b64encode(key))
    return fernet.encrypt(file_data)

def decrypt_file(encrypted_data, key):
    fernet = Fernet(base64.urlsafe_b64encode(key))
    return fernet.decrypt(encrypted_data)