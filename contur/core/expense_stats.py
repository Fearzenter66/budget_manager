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


def get_subcategory_colors(base_color, count):
    if count <= 1:
        return [base_color]

    hex_color = base_color.lstrip('#')
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    colors = []

    for index in range(count):
        factor = 0.45 + (0.55 * index / max(count - 1, 1))
        colors.append(
            '#{:02x}{:02x}{:02x}'.format(
                min(255, int(red + (255 - red) * (1 - factor))),
                min(255, int(green + (255 - green) * (1 - factor))),
                min(255, int(blue + (255 - blue) * (1 - factor))),
            )
        )

    return colors


def get_expenses_by_category(expenses_queryset):
    category_totals = {}
    subcategory_totals = {}

    for expense in expenses_queryset.select_related('subcategory'):
        category = expense.subcategory.decrypted_category
        subcategory_name = expense.subcategory.name
        amount = expense.decrypted_amount

        category_totals[category] = category_totals.get(category, 0) + amount
        subcategory_totals.setdefault(category, {})
        subcategory_totals[category][subcategory_name] = (
            subcategory_totals[category].get(subcategory_name, 0) + amount
        )

    sorted_totals = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
    labels = []
    values = []
    colors = []
    categories = []
    subcategories = {}

    for category, total in sorted_totals:
        labels.append(ExpenseCategory(category).label)
        values.append(float(total))
        colors.append(ExpenseCategory.get_color(category))
        categories.append(category)

        sorted_subcategories = sorted(
            subcategory_totals.get(category, {}).items(),
            key=lambda item: item[1],
            reverse=True,
        )
        base_color = ExpenseCategory.get_color(category)
        sub_labels = [name for name, _ in sorted_subcategories]
        sub_values = [float(value) for _, value in sorted_subcategories]
        sub_colors = get_subcategory_colors(base_color, len(sub_labels))
        subcategories[category] = {
            'labels': sub_labels,
            'values': sub_values,
            'colors': sub_colors,
        }

    return {
        'labels': labels,
        'values': values,
        'colors': colors,
        'categories': categories,
        'subcategories': subcategories,
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
