import base64
import os
from cryptography.fernet import Fernet

secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise ValueError("SECRET_KEY environment variable is not set")

try:
    key = base64.urlsafe_b64decode(secret_key)
except Exception as e:
    raise ValueError("SECRET_KEY is not a valid base64-encoded key") from e

if len(key) != 32:
    raise ValueError("SECRET_KEY must decode to 32 bytes")

cipher_suite = Fernet(secret_key)


def encrypt(data):
    if not isinstance(data, str):
        raise ValueError("Data to encrypt must be a string")
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt(data):
    if not isinstance(data, str):
        raise ValueError("Data to decrypt must be a string")
    try:
        return cipher_suite.decrypt(data.encode()).decode()
    except Exception as e:
        raise ValueError("Failed to decrypt data") from e
