from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import localdate

from core.encryption import (
    decrypt_decimal,
    decrypt_field,
    encrypt_decimal,
    encrypt_field,
    encrypt_value,
    decrypt_value,
)

CURRENCY_CHOICES = (
    ('₽', 'Российский рубль'),
    ('$', 'Американский доллар'),
    ('€', 'Евро'),
)


class ExpenseCategory(models.TextChoices):
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
            decrypted_data.append({
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
            })
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


class Subcategory(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='Пользователь',
    )
    name = models.CharField(max_length=100, verbose_name='Название')
    category = models.TextField(verbose_name='Категория')

    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'

    def save(self, *args, **kwargs):
        category = self.decrypted_category
        ExpenseCategory(category)
        self.category = encrypt_field(category)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_category_display()}: {self.name}'

    @property
    def decrypted_category(self):
        return decrypt_field(self.category)

    def get_category_display(self):
        try:
            return ExpenseCategory(self.decrypted_category).label
        except ValueError:
            return self.decrypted_category

    @property
    def category_color(self):
        return ExpenseCategory.get_color(self.decrypted_category)

    @classmethod
    def get_by_user_name_category(cls, user, name, category):
        name = name.strip()
        for subcategory in cls.objects.filter(user=user, name=name):
            if subcategory.decrypted_category == category:
                return subcategory
        return None

    @classmethod
    def get_or_create_decrypted(cls, user, name, category):
        existing = cls.get_by_user_name_category(user, name, category)
        if existing:
            return existing, False
        subcategory = cls(user=user, name=name.strip(), category=category)
        subcategory.save()
        return subcategory, True


class Expense(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Пользователь',
    )
    amount = models.TextField(verbose_name='Сумма')
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

    def save(self, *args, **kwargs):
        self.amount = encrypt_decimal(self.decrypted_amount)
        self.note = encrypt_field(self.decrypted_note)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.decrypted_amount} {self.currency} ({self.operation_date})'

    @property
    def decrypted_amount(self):
        return decrypt_decimal(self.amount)

    @property
    def decrypted_note(self):
        return decrypt_field(self.note) or ''


class Income(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='incomes',
        verbose_name='Пользователь',
    )
    operation_date = models.DateField(default=localdate, verbose_name='Дата')
    source = models.TextField(verbose_name='Источник дохода')
    amount = models.TextField(verbose_name='Сумма')
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES, verbose_name='Валюта')
    note = models.TextField(blank=True, verbose_name='Пояснение')

    class Meta:
        verbose_name = 'Доход'
        verbose_name_plural = 'Доходы'
        ordering = ['-operation_date', '-id']

    def save(self, *args, **kwargs):
        self.source = encrypt_field(self.decrypted_source)
        self.amount = encrypt_decimal(self.decrypted_amount)
        self.note = encrypt_field(self.decrypted_note)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.decrypted_source}: {self.decrypted_amount} {self.currency} ({self.operation_date})'

    @property
    def decrypted_source(self):
        return decrypt_field(self.source) or ''

    @property
    def decrypted_amount(self):
        return decrypt_decimal(self.amount)

    @property
    def decrypted_note(self):
        return decrypt_field(self.note) or ''
