from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.timezone import localdate

from core.models import CURRENCY_CHOICES, CustomUser, Expense, ExpenseCategory, Income, Subcategory

DATE_INPUT_FORMATS = ['%d/%m/%Y', '%d.%m.%Y']
DATE_INPUT_ATTRS = {
    'class': 'form-input',
    'placeholder': 'дд/мм/гггг',
    'autocomplete': 'off',
    'inputmode': 'numeric',
}


class TransactionFormMixin:
    def __init__(self, user, *args, instance=None, **kwargs):
        self.user = user
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is None:
            self.fields['currency'].initial = user.currency
            self.fields['operation_date'].initial = localdate()


class ExpenseForm(TransactionFormMixin, forms.Form):
    amount = forms.DecimalField(
        label='Сумма',
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0.00',
            'step': '0.01',
        }),
    )
    currency = forms.ChoiceField(
        label='Валюта',
        choices=CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    operation_date = forms.DateField(
        label='Дата операции',
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.DateInput(format='%d/%m/%Y', attrs=DATE_INPUT_ATTRS),
    )
    category = forms.ChoiceField(
        choices=ExpenseCategory.choices,
        widget=forms.HiddenInput(),
    )
    subcategory_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )
    subcategory_name = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input picker-new-field',
            'placeholder': 'Название новой подкатегории',
        }),
    )
    note = forms.CharField(
        label='Пояснение',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Комментарий к операции',
            'rows': 3,
        }),
    )

    def __init__(self, user, *args, instance=None, **kwargs):
        if instance is not None:
            kwargs.setdefault('initial', {}).update({
                'amount': instance.decrypted_amount,
                'currency': instance.currency,
                'operation_date': instance.operation_date,
                'category': instance.subcategory.decrypted_category,
                'subcategory_id': instance.subcategory_id,
                'note': instance.decrypted_note,
            })
        super().__init__(user, *args, instance=instance, **kwargs)
        if not self.initial.get('category'):
            self.initial['category'] = ExpenseCategory.FOOD

    @property
    def category_options(self):
        return [
            {
                'value': choice.value,
                'label': choice.label,
                'color': ExpenseCategory.get_color(choice.value),
            }
            for choice in ExpenseCategory
        ]

    @property
    def subcategories_by_category(self):
        grouped = {}
        for sub in Subcategory.objects.filter(user=self.user).order_by('name'):
            grouped.setdefault(sub.decrypted_category, []).append({
                'id': sub.id,
                'name': sub.name,
                'color': ExpenseCategory.get_color(sub.decrypted_category),
            })
        return grouped

    def clean(self):
        cleaned_data = super().clean()
        subcategory_id = cleaned_data.get('subcategory_id')
        subcategory_name = (cleaned_data.get('subcategory_name') or '').strip()
        category = cleaned_data.get('category')

        if subcategory_id:
            try:
                subcategory = Subcategory.objects.get(
                    pk=subcategory_id,
                    user=self.user,
                )
            except Subcategory.DoesNotExist:
                self.add_error('subcategory_id', 'Выберите существующую подкатегорию.')
            else:
                if subcategory.decrypted_category != category:
                    self.add_error('subcategory_id', 'Выберите существующую подкатегорию.')
                else:
                    cleaned_data['subcategory'] = subcategory
        elif subcategory_name:
            cleaned_data['subcategory_name'] = subcategory_name
        else:
            raise ValidationError('Выберите подкатегорию или создайте новую.')

        return cleaned_data

    def save(self):
        subcategory = self.cleaned_data.get('subcategory')
        if subcategory is None:
            subcategory, _ = Subcategory.get_or_create_decrypted(
                user=self.user,
                category=self.cleaned_data['category'],
                name=self.cleaned_data['subcategory_name'],
            )
        fields = {
            'amount': self.cleaned_data['amount'],
            'currency': self.cleaned_data['currency'],
            'operation_date': self.cleaned_data['operation_date'],
            'note': self.cleaned_data['note'],
            'subcategory': subcategory,
        }
        if self.instance is not None:
            for name, value in fields.items():
                setattr(self.instance, name, value)
            self.instance.save()
            return self.instance
        return Expense.objects.create(user=self.user, **fields)


class IncomeForm(TransactionFormMixin, forms.Form):
    operation_date = forms.DateField(
        label='Дата',
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.DateInput(format='%d/%m/%Y', attrs=DATE_INPUT_ATTRS),
    )
    source = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.HiddenInput(),
    )
    source_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input picker-new-field',
            'placeholder': 'Название нового источника',
        }),
    )
    amount = forms.DecimalField(
        label='Сумма',
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0.00',
            'step': '0.01',
        }),
    )
    currency = forms.ChoiceField(
        label='Валюта',
        choices=CURRENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    note = forms.CharField(
        label='Пояснение',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Комментарий к операции',
            'rows': 3,
        }),
    )

    def __init__(self, user, *args, instance=None, **kwargs):
        if instance is not None:
            kwargs.setdefault('initial', {}).update({
                'operation_date': instance.operation_date,
                'source': instance.decrypted_source,
                'amount': instance.decrypted_amount,
                'currency': instance.currency,
                'note': instance.decrypted_note,
            })
        super().__init__(user, *args, instance=instance, **kwargs)

    @property
    def existing_sources(self):
        from core.expense_stats import INCOME_SOURCE_COLORS

        sources = set()
        for income in Income.objects.filter(user=self.user):
            sources.add(income.decrypted_source)
        return [
            {
                'name': source,
                'color': INCOME_SOURCE_COLORS[index % len(INCOME_SOURCE_COLORS)],
            }
            for index, source in enumerate(sorted(sources))
        ]

    def clean(self):
        cleaned_data = super().clean()
        source = (cleaned_data.get('source') or '').strip()
        source_name = (cleaned_data.get('source_name') or '').strip()

        if source:
            cleaned_data['source'] = source
        elif source_name:
            cleaned_data['source'] = source_name
        else:
            self.add_error('source_name', 'Выберите источник дохода или создайте новый.')

        return cleaned_data

    def save(self):
        fields = {
            'operation_date': self.cleaned_data['operation_date'],
            'source': self.cleaned_data['source'],
            'amount': self.cleaned_data['amount'],
            'currency': self.cleaned_data['currency'],
            'note': self.cleaned_data['note'],
        }
        if self.instance is not None:
            for name, value in fields.items():
                setattr(self.instance, name, value)
            self.instance.save()
            return self.instance
        return Income.objects.create(user=self.user, **fields)


class LoginForm(forms.Form):
    """
    Form for login
    """
    username = forms.CharField(
        label='Имя пользователя',
        max_length=150,
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': 'Имя пользователя',
            'class': 'form-input',
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Пароль',
            'class': 'form-input',
        }),
    )

    def clean_username(self):
        return CustomUser.normalize_username(self.cleaned_data['username'])


class RegisterForm(forms.Form):
    """
    Form for register
    """
    username = forms.CharField(
        label='Имя пользователя',
        max_length=150,
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': 'Имя пользователя',
            'class': 'form-input',
        }),
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Пароль',
            'class': 'form-input',
        }),
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Повторите пароль',
            'class': 'form-input',
        }),
    )

    def clean_username(self):
        """
        Cleans the username
        Returns:
            The cleaned username
        """
        username = CustomUser.normalize_username(self.cleaned_data['username'])
        if CustomUser.get_by_username(username):
            raise ValidationError('Пользователь с таким именем уже существует.')
        return username

    def clean(self):
        """
        Cleans the data
        Returns:
            The cleaned data
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Пароли не совпадают.')

        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error('password1', exc)

        return cleaned_data

    def save(self):
        """
        Saves the user
        Returns:
            The created user
        """
        return CustomUser.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
        )
