import calendar

from django.utils.timezone import localdate

from core.models import ExpenseCategory

PERIOD_CHOICES = (
    ('month', 'Месяц'),
    ('half_year', 'Полгода'),
    ('year', 'Год'),
)

INCOME_SOURCE_COLORS = (
    '#22c55e',
    '#3b82f6',
    '#a855f7',
    '#f59e0b',
    '#06b6d4',
    '#ef4444',
    '#ec4899',
    '#64748b',
    '#14b8a6',
    '#eab308',
)


def subtract_months(reference_date, months):
    year = reference_date.year
    month = reference_date.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(reference_date.day, calendar.monthrange(year, month)[1])
    return reference_date.replace(year=year, month=month, day=day)


def get_period_range(period):
    today = localdate()
    periods = {key: label for key, label in PERIOD_CHOICES}

    if period not in periods:
        period = 'month'

    if period == 'month':
        start = today.replace(day=1)
    elif period == 'half_year':
        start = subtract_months(today.replace(day=1), 5)
    else:
        start = subtract_months(today.replace(day=1), 11)

    return period, start, today, periods[period]


def get_expenses_by_category(expenses_queryset):
    totals = {}
    for expense in expenses_queryset.select_related('subcategory'):
        category = expense.subcategory.decrypted_category
        totals[category] = totals.get(category, 0) + expense.decrypted_amount

    sorted_totals = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    labels = []
    values = []
    colors = []

    for category, total in sorted_totals:
        labels.append(ExpenseCategory(category).label)
        values.append(float(total))
        colors.append(ExpenseCategory.get_color(category))

    return {
        'labels': labels,
        'values': values,
        'colors': colors,
    }


def get_income_by_source(incomes_queryset):
    totals = {}
    for income in incomes_queryset:
        source = income.decrypted_source
        totals[source] = totals.get(source, 0) + income.decrypted_amount

    sorted_totals = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    labels = []
    values = []
    colors = []

    for index, (source, total) in enumerate(sorted_totals):
        labels.append(source)
        values.append(float(total))
        colors.append(INCOME_SOURCE_COLORS[index % len(INCOME_SOURCE_COLORS)])

    return {
        'labels': labels,
        'values': values,
        'colors': colors,
    }


def get_home_charts(user, period='month'):
    period, start, end, period_label = get_period_range(period)

    expenses = user.expenses.filter(
        operation_date__gte=start,
        operation_date__lte=end,
    )
    incomes = user.incomes.filter(
        operation_date__gte=start,
        operation_date__lte=end,
    )

    return {
        'period': period,
        'period_label': period_label,
        'expenses': get_expenses_by_category(expenses),
        'incomes': get_income_by_source(incomes),
    }
