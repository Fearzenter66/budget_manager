from urllib.parse import urlencode

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from core.auth_backend import EncryptedUsernameBackend
from core.expense_stats import PERIOD_CHOICES, get_home_charts, get_period_range
from core.models import CURRENCY_CHOICES, CustomUser, Expense, ExpenseCategory, Income, Subcategory
from core.money import get_display_currency
from core.web.forms import ExpenseForm, IncomeForm, LoginForm, RegisterForm


def _get_period(request):
    period = request.GET.get('period') or request.POST.get('period', 'month')
    if period not in dict(PERIOD_CHOICES):
        return 'month'
    return period


def _get_category(request):
    category = request.GET.get('category') or request.POST.get('category', '')
    if category in ExpenseCategory.values:
        return category
    return ''


def _build_list_query(request, **extra):
    params = {'period': _get_period(request)}
    category = _get_category(request)
    if category:
        params['category'] = category
    for key, value in extra.items():
        if value not in (None, ''):
            params[key] = value
    return urlencode(params)


def _period_redirect(request, view_name, **kwargs):
    url = reverse(view_name, kwargs=kwargs)
    return redirect(f'{url}?{_build_list_query(request)}')


def _list_period_context(request, queryset):
    period = _get_period(request)
    period, start, end, period_label = get_period_range(period)
    records = queryset.filter(
        operation_date__gte=start,
        operation_date__lte=end,
        currency=get_display_currency(request),
    )
    return {
        'username': request.user.get_decrypted_username(),
        'period': period,
        'period_choices': PERIOD_CHOICES,
        'period_label': period_label,
        'list_query': _build_list_query(request),
        'records': records,
    }


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
    period = request.GET.get('period', 'month')
    if period not in dict(PERIOD_CHOICES):
        period = 'month'

    charts = get_home_charts(request.user, period, currency=get_display_currency(request))
    return render(request, 'home.html', {
        'username': request.user.get_decrypted_username(),
        'period': charts['period'],
        'period_choices': PERIOD_CHOICES,
        'period_label': charts['period_label'],
        'expenses_chart': charts['expenses'],
        'incomes_chart': charts['incomes'],
        'expenses_total': charts['expenses_total'],
        'incomes_total': charts['incomes_total'],
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
def add_expense_view(request):
    form = ExpenseForm(request.user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('web:home')

    return render(request, 'expense_add.html', {
        'username': request.user.get_decrypted_username(),
        'form': form,
    })


@login_required
def add_income_view(request):
    form = IncomeForm(request.user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('web:home')

    return render(request, 'income_add.html', {
        'username': request.user.get_decrypted_username(),
        'form': form,
    })


def _expense_list_context(request, edit_form=None, editing_id=None):
    context = _list_period_context(request, request.user.expenses.select_related('subcategory'))
    category = _get_category(request)
    records = context['records']
    if category:
        subcategory_ids = [
            subcategory.id
            for subcategory in Subcategory.objects.filter(user=request.user)
            if subcategory.decrypted_category == category
        ]
        records = records.filter(subcategory_id__in=subcategory_ids)
    context.update({
        'edit_form': edit_form,
        'editing_id': editing_id,
        'category': category,
        'category_label': dict(ExpenseCategory.choices).get(category, ''),
        'category_options': [
            {
                'value': choice.value,
                'label': choice.label,
                'color': ExpenseCategory.get_color(choice.value),
            }
            for choice in ExpenseCategory
        ],
        'records': records,
    })
    return context


def _income_list_context(request, edit_form=None, editing_id=None):
    context = _list_period_context(request, request.user.incomes)
    context.update({
        'edit_form': edit_form,
        'editing_id': editing_id,
    })
    return context


@login_required
def expense_list_view(request):
    edit_form = None
    editing_id = None
    edit_pk = request.GET.get('edit')
    if edit_pk:
        expense = Expense.objects.filter(pk=edit_pk, user=request.user).first()
        if expense is not None:
            edit_form = ExpenseForm(request.user, instance=expense)
            editing_id = expense.id
    return render(request, 'expense_list.html', _expense_list_context(
        request,
        edit_form=edit_form,
        editing_id=editing_id,
    ))


@login_required
def income_list_view(request):
    edit_form = None
    editing_id = None
    edit_pk = request.GET.get('edit')
    if edit_pk:
        income = Income.objects.filter(pk=edit_pk, user=request.user).first()
        if income is not None:
            edit_form = IncomeForm(request.user, instance=income)
            editing_id = income.id
    return render(request, 'income_list.html', _income_list_context(
        request,
        edit_form=edit_form,
        editing_id=editing_id,
    ))


@login_required
def edit_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method != 'POST':
        url = reverse('web:expense_list')
        return redirect(f'{url}?{_build_list_query(request, edit=pk)}')

    form = ExpenseForm(request.user, request.POST, instance=expense)
    if form.is_valid():
        form.save()
        return _period_redirect(request, 'web:expense_list')

    return render(request, 'expense_list.html', _expense_list_context(
        request,
        edit_form=form,
        editing_id=expense.id,
    ))


@login_required
def edit_income_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method != 'POST':
        url = reverse('web:income_list')
        return redirect(f'{url}?{_build_list_query(request, edit=pk)}')

    form = IncomeForm(request.user, request.POST, instance=income)
    if form.is_valid():
        form.save()
        return _period_redirect(request, 'web:income_list')

    return render(request, 'income_list.html', _income_list_context(
        request,
        edit_form=form,
        editing_id=income.id,
    ))


@login_required
@require_POST
def delete_expense_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    return _period_redirect(request, 'web:expense_list')


@login_required
@require_POST
def delete_income_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    income.delete()
    return _period_redirect(request, 'web:income_list')


@login_required
@require_GET
def set_balance_currency_view(request):
    currency = request.GET.get('currency')
    if currency in dict(CURRENCY_CHOICES):
        request.session['balance_currency'] = currency

    next_url = request.GET.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('web:home')


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
