import os
from decimal import Decimal, InvalidOperation

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
DATA_KEY = os.getenv('DATA_KEY')

if DATA_KEY is None:
    raise ImproperlyConfigured('Encryption key not found.')


def encrypt_value(value):
    if value is None or not isinstance(value, str):
        return None
    return Fernet(DATA_KEY.encode()).encrypt(value.encode()).decode()


def decrypt_value(value):
    if value is None or not isinstance(value, str):
        return None
    try:
        return Fernet(DATA_KEY.encode()).decrypt(value.encode()).decode()
    except (InvalidToken, ValueError):
        return None


def is_encrypted(value):
    if not value or not isinstance(value, str):
        return False
    try:
        Fernet(DATA_KEY.encode()).decrypt(value.encode())
        return True
    except (InvalidToken, ValueError):
        return False


def encrypt_field(value):
    if value is None:
        return None
    if value == '':
        return ''
    if is_encrypted(value):
        return value
    return encrypt_value(str(value))


def decrypt_field(value):
    if value is None or value == '':
        return value
    decrypted = decrypt_value(value)
    return decrypted if decrypted is not None else value


def encrypt_decimal(value):
    if value is None:
        return None
    if isinstance(value, str) and is_encrypted(value):
        return value
    return encrypt_field(str(value))


def decrypt_decimal(value):
    decrypted = decrypt_field(value)
    if decrypted in (None, ''):
        return Decimal('0')
    try:
        return Decimal(decrypted)
    except (InvalidOperation, ValueError):
        return Decimal('0')
