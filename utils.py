from cryptography.fernet import Fernet
import os

secret_key = os.getenv("DJANGO_SECRET_KEY")
cipher_suite = Fernet(secret_key.encode())


def encrypt(data):
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt(data):
    return cipher_suite.decrypt(data.encode()).decode()
