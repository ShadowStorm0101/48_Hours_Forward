from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet


def hash_password(plain_password: str, pepper: str) -> str:
    return generate_password_hash(plain_password + pepper)


def verify_password(plain_password: str, stored_hash: str, pepper: str) -> bool:
    return check_password_hash(stored_hash, plain_password + pepper)


def _get_fernet(key: str) -> Fernet:
    return Fernet(key.encode())


def encrypt_bio(plain_bio: str, key: str) -> str:
    f = _get_fernet(key)
    token = f.encrypt(plain_bio.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_bio(token: str, key: str) -> str:
    f = _get_fernet(key)
    plain_bytes = f.decrypt(token.encode("utf-8"))
    return plain_bytes.decode("utf-8")
