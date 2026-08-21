from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.auth_backend import EncryptedUsernameBackend
from core.models import CustomUser
from core.web.forms import LoginForm, RegisterForm


def welcome(request):
    """
    The redirect to the home page if the user is authenticated, otherwise the welcome page
    """
    if request.user.is_authenticated:
        return redirect('web:home')
    return render(request, 'welcome.html')


@login_required
def home(request):
    """
    Renders the home page
    """
    return render(request, 'home.html', {
        'username': request.user.get_decrypted_username(),
    })


def login_view(request):
    """
    Renders the login page
    """
    if request.user.is_authenticated:
        return redirect('web:home')

    show_password_recovery = False
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = CustomUser.get_by_username(username)
        if user is None:
            form.add_error(None, 'Неверное имя пользователя или пароль.')
        else:
            if user.check_password(password):
                login(request, user, backend='core.auth_backend.EncryptedUsernameBackend')
                return redirect('web:home')
            form.add_error(None, 'Неверный пароль.')
            show_password_recovery = True

    return render(request, 'login.html', {
        'form': form,
        'show_password_recovery': show_password_recovery,
    })


def register_view(request):
    """
    Renders the register page
    """
    if request.user.is_authenticated:
        return redirect('web:home')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='core.auth_backend.EncryptedUsernameBackend')
        return redirect('web:home')

    return render(request, 'register.html', {'form': form})


@login_required
def settings_view(request):
    """
    Renders the settings page
    """
    return render(request, 'settings.html', {
        'username': request.user.get_decrypted_username(),
    })


def logout_view(request):
    """
    Logs out the user and redirects to the welcome page
    """
    logout(request)
    return redirect('web:welcome')


def password_reset_view(request):
    """
    Renders the password reset page
    """
    return render(request, 'password_reset.html')
