from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from core.models import CURRENCY_CHOICES


def get_display_currency(request):
    user = getattr(request, 'user', None)
    allowed = dict(CURRENCY_CHOICES)
    default = '₽'

    if user is None or not getattr(user, 'is_authenticated', False):
        return default

    currency = request.session.get('balance_currency') or user.currency
    if currency in allowed:
        return currency
    if user.currency in allowed:
        return user.currency
    return default


def format_amount(value):
    if value in (None, ''):
        amount = Decimal('0')
    else:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            amount = Decimal('0')

    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    sign = '-' if amount < 0 else ''
    amount = abs(amount)
    integer_part, _, fraction_part = f'{amount:.2f}'.partition('.')
    groups = []
    while integer_part:
        groups.append(integer_part[-3:])
        integer_part = integer_part[:-3]
    return f"{sign}{' '.join(reversed(groups))}.{fraction_part}"
