from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.models import CustomUser


class LoginForm(forms.Form):
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
        username = CustomUser.normalize_username(self.cleaned_data['username'])
        if CustomUser.get_by_username(username):
            raise ValidationError('Пользователь с таким именем уже существует.')
        return username

    def clean(self):
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
        return CustomUser.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
        )
