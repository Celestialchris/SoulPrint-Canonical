from cryptography.fernet import Fernet
import os

key = os.getenv("ENCRYPTION_KEY")
cipher_suite = Fernet(key.encode()) if key else None


def encrypt_message(message: str) -> bytes:
    if not cipher_suite:
        return message.encode()
    return cipher_suite.encrypt(message.encode())


def decrypt_message(encrypted_message: bytes) -> str:
    if not cipher_suite:
        return encrypted_message.decode()
    return cipher_suite.decrypt(encrypted_message).decode()
