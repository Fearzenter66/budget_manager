import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from enum import Enum
from django.core.exceptions import ValidationError, ImproperlyConfigured
from cryptography.fernet import Fernet
from dotenv import load_dotenv

#region Hashing personal data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))  # Loading environment variables
DATA_KEY = os.getenv('DATA_KEY', None)

if DATA_KEY is None:
    raise ImproperlyConfigured("Encryption key not found.")

def encrypt_value(value):
    cipher_suite = Fernet(DATA_KEY.encode())  # Using globaly variable DATA_KEY
    if value is None or not isinstance(value, str):
        return None
    return cipher_suite.encrypt(value.encode()).decode()

def decrypt_value(value):
    cipher_suite = Fernet(DATA_KEY.encode())  # Similarly for decryption
    if value is None or not isinstance(value, str):
        return None
    try:
        return cipher_suite.decrypt(value.encode()).decode()
    except Exception as e:
        print(f'Decryption error: {e}')
        return None
#endregion

class CustomUser(AbstractUser):
    """
        Model <<User>>

        - currency: user`s default currency
        - updated: last user`s data update date
        - deleted: date the user was deleted
    """
    currency = models.CharField(max_length=20, choices=(('₽', 'Российский рубль'), ('$', 'Американский доллар'), ('€', "Евро")), default='₽')
    is_email_verified = models.BooleanField(null=False, default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set', 
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set', 
        related_query_name='customuser',
    )

    updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(null=False, default=False)

    def save(self, *args, **kwargs):
        if self.username:
            self.username = encrypt_value(self.normalize_username(self.username))
        self.email = encrypt_value(self.email)
        self.first_name = encrypt_value(self.first_name)
        self.last_name = encrypt_value(self.last_name)

        super().save(*args, **kwargs)

    @classmethod
    def decrypted_objects(cls):
        queryset = cls.objects.all()
        decrypted_data = []
        for obj in queryset:
            data = {
                'id': obj.id,
                'first_name': decrypt_value(obj.first_name),
                'last_name': decrypt_value(obj.last_name),
                'email': decrypt_value(obj.email),
                'username': decrypt_value(obj.username),
                'currency': obj.currency,
                'date_joined': obj.date_joined,
                'last_login': obj.last_login,
                'is_active': obj.is_active,
                'is_staff': obj.is_staff,
                'is_superuser': obj.is_superuser,
                'is_email_verified': obj.is_email_verified,
                'updated': obj.updated,
                'deleted': obj.deleted,
            }
            decrypted_data.append(data)
        return decrypted_data

    @staticmethod
    def normalize_username(username):
        return username.strip().lower()

    @classmethod
    def get_by_username(cls, username):
        username = cls.normalize_username(username)
        for user in cls.objects.filter(deleted=False):
            if decrypt_value(user.username) == username:
                return user
        return None

    def get_decrypted_username(self):
        return decrypt_value(self.username)
