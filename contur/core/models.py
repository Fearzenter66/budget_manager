import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import localdate
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
    """
    Encrypts a value using the globaly defined DATA_KEY
    Args:
        value: The value to encrypt
    Returns:
        The encrypted value
    """
    cipher_suite = Fernet(DATA_KEY.encode())  # Using globaly variable DATA_KEY
    if value is None or not isinstance(value, str):
        return None
    return cipher_suite.encrypt(value.encode()).decode()

def decrypt_value(value):
    """
    Decrypts a value using the globaly defined DATA_KEY
    Args:
        value: The value to decrypt
    Returns:
        The decrypted value
    """
    cipher_suite = Fernet(DATA_KEY.encode())  # Similarly for decryption
    if value is None or not isinstance(value, str):
        return None
    try:
        return cipher_suite.decrypt(value.encode()).decode()
    except Exception as e:
        print(f'Decryption error: {e}')
        return None
#endregion

CURRENCY_CHOICES = (
    ('₽', 'Российский рубль'),
    ('$', 'Американский доллар'),
    ('€', 'Евро'),
)


class ExpenseCategory(models.TextChoices):
    """
    Категории расходов.

    У каждого элемента два значения:
    - первое ('food') — код, который хранится в базе данных;
    - второе ('Еда') — подпись, которую видит пользователь.

    В коде: ExpenseCategory.FOOD -> 'food', ExpenseCategory.FOOD.label -> 'Еда'
    У модели: obj.get_category_display() -> 'Еда'
    """
    FOOD = 'food', 'Еда'
    HOME = 'home', 'Дом'
    PERSONAL = 'personal', 'На себя'
    TRANSPORT = 'transport', 'Транспорт'
    HEALTH = 'health', 'Здоровье'
    LEISURE = 'leisure', 'Отдых'
    BAD_HABITS = 'bad_habits', 'Вредные привычки'
    OTHER = 'other', 'Прочее'

    @classmethod
    def get_color(cls, value):
        try:
            return EXPENSE_CATEGORY_COLORS[cls(value)]
        except (KeyError, ValueError):
            return EXPENSE_CATEGORY_COLORS[cls.OTHER]


EXPENSE_CATEGORY_COLORS = {
    ExpenseCategory.FOOD: '#22c55e',
    ExpenseCategory.HOME: '#3b82f6',
    ExpenseCategory.PERSONAL: '#a855f7',
    ExpenseCategory.TRANSPORT: '#f59e0b',
    ExpenseCategory.HEALTH: '#ef4444',
    ExpenseCategory.LEISURE: '#06b6d4',
    ExpenseCategory.BAD_HABITS: '#78716c',
    ExpenseCategory.OTHER: '#64748b',
}


class CustomUser(AbstractUser):
    """
        Model <<User>>

        - currency: user`s default currency
        - updated: last user`s data update date
        - deleted: date the user was deleted
    """
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, default='₽')
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
        """
        Saves the user to the database
        Encrypts the username, email, first name and last name
        """
        if self.username:
            self.username = encrypt_value(self.normalize_username(self.username))
        self.email = encrypt_value(self.email)
        self.first_name = encrypt_value(self.first_name)
        self.last_name = encrypt_value(self.last_name)

        super().save(*args, **kwargs)

    @classmethod
    def decrypted_objects(cls):
        """
        Returns a list of decrypted parameters of the user
        """
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
        """
        Normalizes the username
        Args:
            username: The username to normalize
        Returns:
            The normalized username (lowercase and stripped)
        """
        return username.strip().lower()

    @classmethod
    def get_by_username(cls, username):
        """
        Gets a user by decrypted username
        Args:
            username: The username to get the user by
        Returns:
            The user if found, otherwise None
        """
        username = cls.normalize_username(username)
        for user in cls.objects.filter(deleted=False):
            if decrypt_value(user.username) == username:
                return user
        return None

    def get_decrypted_username(self):
        """
        Gets the decrypted username
        Returns:
            The decrypted username
        """
        return decrypt_value(self.username)


class Subcategory(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='Пользователь',
    )
    name = models.CharField(max_length=100, verbose_name='Название')
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, verbose_name='Категория')

    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'category'],
                name='unique_user_subcategory',
            ),
        ]

    def __str__(self):
        return f'{self.get_category_display()}: {self.name}'

    @property
    def category_color(self):
        return ExpenseCategory.get_color(self.category)


class Expense(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Пользователь',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, verbose_name='Валюта')
    operation_date = models.DateField(default=localdate, verbose_name='Дата операции')
    note = models.TextField(blank=True, verbose_name='Пояснение')
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.PROTECT,
        related_name='expenses',
        verbose_name='Подкатегория',
    )

    class Meta:
        verbose_name = 'Трата'
        verbose_name_plural = 'Траты'
        ordering = ['-operation_date', '-id']

    def __str__(self):
        return f'{self.amount} {self.currency} ({self.operation_date})'


class Income(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='incomes',
        verbose_name='Пользователь',
    )
    operation_date = models.DateField(default=localdate, verbose_name='Дата')
    source = models.CharField(max_length=200, verbose_name='Источник дохода')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, verbose_name='Валюта')
    note = models.TextField(blank=True, verbose_name='Пояснение')

    class Meta:
        verbose_name = 'Доход'
        verbose_name_plural = 'Доходы'
        ordering = ['-operation_date', '-id']

    def __str__(self):
        return f'{self.source}: {self.amount} {self.currency} ({self.operation_date})'
