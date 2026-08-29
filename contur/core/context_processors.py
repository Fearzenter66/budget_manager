from decimal import Decimal

from core.models import CURRENCY_CHOICES
from core.money import get_display_currency


def _sum_in_currency(queryset, currency):
    total = Decimal('0')
    for item in queryset.filter(currency=currency):
        total += item.decrypted_amount
    return total


def balance(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}

    currency = get_display_currency(request)
    income_total = _sum_in_currency(user.incomes, currency)
    expense_total = _sum_in_currency(user.expenses, currency)
    value = income_total - expense_total

    return {
        'balance': value,
        'balance_currency': currency,
        'balance_currency_choices': CURRENCY_CHOICES,
        'balance_is_negative': value < 0,
        'balance_is_positive': value > 0,
    }
